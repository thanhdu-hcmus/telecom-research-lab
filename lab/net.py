"""The sole research HTTP boundary: allowlists, redirects, limits and cache."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import httpx

from lab.io import LabError, load, save

DENIED = ("sci-hub", "scihub", "libgen", "librarygenesis", "annas-archive", "annasarchive",
          "z-library", "zlibrary", "z-lib", "researchgate.net")


def validate_url(url: str, allowed: set[str]) -> str:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    decoded = unquote(host)
    if any(word in decoded for word in DENIED):
        raise LabError("Forbidden automated source")
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise LabError("Only HTTPS without credentials on the standard port is allowed")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise LabError("Literal IP destinations are not permitted")
    if not re.fullmatch(r"[a-z0-9.-]+", host) or host not in allowed:
        raise LabError(f"Host requires explicit institutional/publisher OA review: {host}")
    return host


class Network:
    def __init__(self, repo: Path, transport=None, sleeper=time.sleep, clock=time.monotonic):
        self.config = load(repo / "config/sources.yaml")
        self.allowed = set(self.config["allow_hosts"] + self.config.get("approved_oa_hosts", []))
        self.cache = repo / ".cache/http"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=self.config["timeout_s"], follow_redirects=False,
                                   transport=transport, headers={"User-Agent": "telecom-research-lab/0.1"})
        self.sleep, self.clock = sleeper, clock
        self.last: dict[str, float] = {}

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def get(self, url: str, params: dict | None = None, headers: dict | None = None,
            cache: bool = True) -> httpx.Response:
        request_url = str(httpx.URL(url, params=params)) if params else url
        validate_url(request_url, self.allowed)
        key = hashlib.sha256((request_url + json.dumps(headers or {}, sort_keys=True)).encode()).hexdigest()
        body_path, meta_path = self.cache / (key + ".bin"), self.cache / (key + ".json")
        if cache and body_path.exists() and meta_path.exists():
            meta = load(meta_path)
            if time.time() - meta["retrieved"] < self.config["cache_hours"] * 3600:
                validate_url(meta["final_url"], self.allowed)
                body = body_path.read_bytes()
                if hashlib.sha256(body).hexdigest() == meta["sha256"]:
                    return httpx.Response(200, content=body, headers=meta["headers"], request=httpx.Request("GET", meta["final_url"]))
        current = request_url
        retries = self.config["retries"]
        for _hop in range(6):
            host = validate_url(current, self.allowed)
            minimum_interval = 3.0 if host in {"export.arxiv.org", "arxiv.org"} else 1 / self.config["requests_per_second"]
            response = None
            for attempt in range(retries + 1):
                delay = minimum_interval - (self.clock() - self.last.get(host, -1e9))
                if delay > 0:
                    self.sleep(delay)
                self.last[host] = self.clock()
                try:
                    with self.client.stream("GET", current, headers=headers or {}) as stream:
                        data = bytearray()
                        for block in stream.iter_bytes():
                            data.extend(block)
                            if len(data) > self.config["maximum_response_bytes"]:
                                raise LabError("Response exceeds configured size limit")
                        decoded_headers = {k: v for k, v in stream.headers.items() if k.lower() not in {"content-encoding", "content-length"}}
                        response = httpx.Response(stream.status_code, headers=decoded_headers,
                                                  content=bytes(data), request=stream.request)
                except httpx.TransportError:
                    if attempt == retries:
                        raise LabError(f"Network unavailable for {host}; use the approved host route") from None
                    self.sleep(min(2 ** attempt, 10))
                    continue
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < retries:
                        retry_after = response.headers.get("retry-after", "")
                        self.sleep(min(float(retry_after) if retry_after.isdigit() else 2 ** attempt, 10))
                        continue
                break
            if response.is_redirect:
                target = urljoin(current, response.headers.get("location", ""))
                validate_url(target, self.allowed)  # Validate BEFORE contacting next hop.
                if urlsplit(target).hostname != urlsplit(current).hostname:
                    headers = None  # Never forward optional API credentials across hosts.
                current = target
                continue
            if response.status_code >= 400:
                raise LabError(f"HTTP {response.status_code} from {host}")
            if cache:
                body_path.write_bytes(response.content)
                clean_url = str(httpx.URL(current).copy_with(query=None))
                save(meta_path, {"retrieved": time.time(), "final_url": clean_url,
                                 "headers": {"content-type": response.headers.get("content-type", "")},
                                 "sha256": hashlib.sha256(response.content).hexdigest()})
            return response
        raise LabError("Too many redirects; retrieval stopped")

    def json(self, url: str, **kwargs):
        try:
            return self.get(url, **kwargs).json()
        except json.JSONDecodeError:
            raise LabError("Source returned malformed JSON") from None
