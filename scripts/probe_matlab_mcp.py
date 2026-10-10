"""Exercise the official MATLAB MCP Server directly using JSON-RPC stdio.

This tests the installed server and MATLAB together; it does not pretend the
currently running Codex session can hot-reload a newly registered MCP server.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
import tomllib

from probe_environment import ROOT, redact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", choices=["sandbox", "host"], required=True)
    args = parser.parse_args()
    config = tomllib.loads((ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    server = config["mcp_servers"]["matlab"]
    process = subprocess.Popen(
        [server["command"], *server["args"]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    replies: queue.Queue = queue.Queue()
    errors = []

    def read_stdout():
        for line in process.stdout:
            try:
                replies.put(json.loads(line))
            except json.JSONDecodeError:
                errors.append(redact(line))

    def read_stderr():
        for line in process.stderr:
            errors.append(redact(line))

    threading.Thread(target=read_stdout, daemon=True).start()
    threading.Thread(target=read_stderr, daemon=True).start()
    sequence = 0
    transcript = []

    def send(message):
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def request(method, params):
        nonlocal sequence
        sequence += 1
        request_id = sequence
        send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            try:
                message = replies.get(timeout=min(1, deadline - time.monotonic()))
            except queue.Empty:
                if process.poll() is not None:
                    raise RuntimeError(f"MCP server exited with code {process.returncode}")
                continue
            if message.get("method") == "roots/list" and "id" in message:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {
                            "roots": [{"uri": ROOT.as_uri(), "name": "telecom-research-lab"}]
                        },
                    }
                )
                continue
            transcript.append(message)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message.get("result", {})
        raise TimeoutError(f"No MCP response for {method}")

    result = {"context": args.context, "status": "FAIL"}
    try:
        result["initialize"] = request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": False}},
                "clientInfo": {"name": "telecom-lab-m0-probe", "version": "0.1.0"},
            },
        )
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = request("tools/list", {})
        result["tools"] = tools.get("tools", [])
        names = [tool["name"] for tool in result["tools"]]
        if "evaluate_matlab_code" not in names:
            raise RuntimeError("Expected evaluate_matlab_code tool not found")
        result["evaluation"] = request(
            "tools/call",
            {
                "name": "evaluate_matlab_code",
                "arguments": {
                    "code": "disp(1); assert(2+2==4); fprintf('MATLAB_MCP_SMOKE_PASS\\n');"
                },
            },
        )
        evaluation = result["evaluation"]
        text = "\n".join(item.get("text", "") for item in evaluation.get("content", []))
        if evaluation.get("isError") or "MATLAB_MCP_SMOKE_PASS" not in text:
            raise RuntimeError("MATLAB MCP evaluation did not produce its success sentinel")
        result["status"] = "PASS"
    except (OSError, RuntimeError, TimeoutError) as exc:
        result["reason"] = redact(str(exc))
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
        result["stderr"] = errors
        result["transcript"] = transcript
        target = ROOT / "docs" / "evidence" / f"matlab-mcp-{args.context}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            redact(json.dumps(result, indent=2)) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps({k: v for k, v in result.items() if k in {"status", "context", "reason"}}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
