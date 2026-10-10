"""Official installed MATLAB MCP server over its documented JSON-RPC stdio."""

import json
import queue
import subprocess
import threading
import time
import tomllib

from lab.io import LabError


def evaluate(repo, code, timeout=180):
    cfg = tomllib.loads((repo / ".codex/config.toml").read_text(encoding="utf-8"))["mcp_servers"][
        "matlab"
    ]
    process = subprocess.Popen(
        [cfg["command"], *cfg["args"]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    replies = queue.Queue()
    errors = []
    sequence = 0

    def read_output():
        for line in process.stdout:
            try:
                replies.put(json.loads(line))
            except ValueError:
                errors.append(line.strip())

    def read_errors():
        for line in process.stderr:
            errors.append(line.strip())

    threading.Thread(target=read_output, daemon=True).start()
    threading.Thread(target=read_errors, daemon=True).start()

    def send(value):
        process.stdin.write(json.dumps(value) + "\n")
        process.stdin.flush()

    def request(method, params):
        nonlocal sequence
        sequence += 1
        identifier = sequence
        send({"jsonrpc": "2.0", "id": identifier, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                value = replies.get(timeout=1)
            except queue.Empty:
                if process.poll() is not None:
                    raise LabError("MATLAB MCP exited before reply")
                continue
            if value.get("method") == "roots/list" and "id" in value:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": value["id"],
                        "result": {
                            "roots": [{"uri": repo.as_uri(), "name": "telecom-research-lab"}]
                        },
                    }
                )
            if value.get("id") == identifier:
                if "error" in value:
                    raise LabError(str(value["error"]))
                return value.get("result", {})
        raise LabError("MATLAB MCP request timed out")

    try:
        request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": False}},
                "clientInfo": {"name": "telecom-lab", "version": "0.1.0"},
            },
        )
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        names = [t["name"] for t in request("tools/list", {}).get("tools", [])]
        if "evaluate_matlab_code" not in names:
            raise LabError("Installed server lacks evaluate_matlab_code")
        result = request(
            "tools/call", {"name": "evaluate_matlab_code", "arguments": {"code": code}}
        )
        if result.get("isError"):
            raise LabError("MATLAB evaluation failed: " + str(result.get("content")))
        return {"result": result, "server_stderr": errors}
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
