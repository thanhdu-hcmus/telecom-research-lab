import gzip
from pathlib import Path

import httpx
import pytest

from lab.io import LabError, load, save
from lab.net import Network, validate_url

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def configured(tmp_path):
    settings = load(ROOT / "config/sources.yaml")
    settings["retries"] = 1
    settings["requests_per_second"] = 100000
    save(tmp_path / "config/sources.yaml", settings)
    return tmp_path


@pytest.mark.parametrize(
    "url",
    [
        "https://sci-hub.se/a",
        "https://libgen.is/a",
        "https://annas-archive.org/a",
        "https://z-library.sk/a",
        "https://researchgate.net/a",
        "http://arxiv.org/a",
        "https://api.openalex.org.evil.test/a",
        "https://user:password@arxiv.org/a",  # pragma: allowlist secret
        "https://arxiv.org:444/a",
        "https://127.0.0.1/a",
    ],
)
def test_policy_rejects_before_network(url):
    with pytest.raises(LabError):
        validate_url(url, {"arxiv.org", "127.0.0.1", "sci-hub.se"})


def test_redirect_to_denied_and_unknown_host_has_zero_calls(configured):
    for host in ["sci-hub.se", "unreviewed-publisher.example"]:
        contacted = []

        def handler(request):
            contacted.append(request.url.host)
            return httpx.Response(302, headers={"location": f"https://{host}/paper.pdf"})

        with Network(configured, httpx.MockTransport(handler), sleeper=lambda _: None) as net:
            with pytest.raises(LabError):
                net.get("https://arxiv.org/pdf/1234.5678")
        assert contacted == ["arxiv.org"]


def test_retry_cache_gzip_and_rate_limit(configured):
    calls, delays = [], []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "1"})
        return httpx.Response(
            200,
            content=gzip.compress(b'{"results": []}'),
            headers={"content-encoding": "gzip", "content-type": "application/json"},
        )

    with Network(
        configured, httpx.MockTransport(handler), sleeper=delays.append, clock=lambda: 1
    ) as net:
        assert net.json("https://api.openalex.org/works") == {"results": []}
        assert net.json("https://api.openalex.org/works") == {"results": []}
    assert len(calls) == 2
    assert delays


def test_response_limit_and_redirect_credential_drop(configured):
    settings = load(configured / "config/sources.yaml")
    settings["maximum_response_bytes"] = 20
    save(configured / "config/sources.yaml", settings)
    with Network(
        configured, httpx.MockTransport(lambda _: httpx.Response(200, content=b"x" * 21))
    ) as net:
        with pytest.raises(LabError, match="limit"):
            net.get("https://api.openalex.org/works")
    contacted = []

    def handler(request):
        contacted.append(request)
        if request.url.host == "api.openalex.org":
            return httpx.Response(302, headers={"location": "https://arxiv.org/pdf/a"})
        return httpx.Response(200, content=b"okay")

    with Network(configured, httpx.MockTransport(handler), sleeper=lambda _: None) as net:
        net.get("https://api.openalex.org/works", headers={"x-api-key": "fixture-only"})
    assert "x-api-key" not in contacted[1].headers
