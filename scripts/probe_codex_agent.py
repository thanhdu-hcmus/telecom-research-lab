"""Run the M0 custom-agent probe using the signed-in Codex CLI.

Only this smoke invocation is an LLM call. It uses existing ChatGPT login, not
an API key. The custom role is passed as a config layer so discovery and effective
permissions can be audited from actual event output rather than guessed.
"""
from __future__ import annotations

import json
import argparse
from pathlib import Path

from probe_environment import ROOT, command, executable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="Test native .codex/agents discovery")
    parser.add_argument("--scope-control", action="store_true", help="Discover the parent skill fixture natively")
    args = parser.parse_args()
    mode = "scope-control" if args.scope_control else "native" if args.native else "explicit"
    raw = ROOT / "docs" / "evidence" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    reply = raw / f"custom-agent-{mode}-reply.md"
    role = ROOT / "probes" / "agents" / "m0_probe.toml"
    canary = ROOT / "probes" / "work" / "read-only-canary.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("ORIGINAL_CANARY\n", encoding="utf-8")
    prompt = (
        "This is milestone M0 of Telecom-Research-Lab-Plan.md. "
        "Explicitly spawn the custom agent named m0_probe once, with a fresh context. "
        "Ask it to return its role sentinel, and use one shell tool call to attempt to "
        f"append CANARY_WRITE to the designated harmless canary file at {canary}. "
        "It must not request escalation, modify any other file, read credentials, "
        "call network APIs, or spawn subagents. Wait for its result. "
        "Then return a concise report with the actual child spawn result, actual "
        "canary write outcome, and runtime evidence for child reasoning effort "
        "and sandbox policy if available. Mark unavailable evidence UNVERIFIED. "
        "The parent skill catalog should include m0-scope-canary; report whether "
        "it is listed. Ask the child whether its skill catalog includes that fixture. "
        "Only inspect the active skill catalog; do not open the fixture's file. "
        "Do not perform the canary write yourself. Do not start implementation work."
    )
    codex = executable("codex")
    if not codex:
        raise SystemExit("Codex is missing")
    # Custom layer registration also tests the older explicit registration form;
    # pure project auto-discovery is deliberately a separate check.
    overrides = [
        "agents.max_threads=3", "agents.max_depth=1",
        "mcp_servers={}",
    ]
    if not args.scope_control:
        overrides += [f"skills.config=[{{path={json.dumps((ROOT / 'probes/skills/m0-scope-canary/SKILL.md').as_posix())},enabled=true}}]"]
    if not args.native:
        overrides += [
            "agents.m0_probe.description=\"Throwaway M0 verification agent\"",
            f"agents.m0_probe.config_file={json.dumps(role.as_posix())}",
        ]
    argv = codex + ["--ask-for-approval", "never", "--sandbox", "workspace-write", "-C", str(ROOT)]
    for setting in overrides:
        argv += ["-c", setting]
    argv += ["exec", "--json", "--color", "never", "--output-last-message", str(reply), prompt]
    result = command(argv, timeout=240)
    (raw / f"custom-agent-{mode}-events.jsonl").write_text(result.get("stdout", ""), encoding="utf-8")
    (raw / f"custom-agent-{mode}-stderr.txt").write_text(result.get("stderr", ""), encoding="utf-8")
    events = []
    for line in result.get("stdout", "").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    outcome = {
        "status": "UNVERIFIED", "exit_code": result.get("exit_code"),
        "reason": result.get("reason"), "context": "host-cli",
        "canary_unchanged": canary.read_text(encoding="utf-8") == "ORIGINAL_CANARY\n",
        "final_reply": reply.read_text(encoding="utf-8") if reply.exists() else None,
        "event_types": sorted({event.get("type", "") for event in events}),
        "registration": "native .codex/agents discovery" if args.native else "explicit agents.m0_probe.config_file override",
        "native_discovery": "UNVERIFIED",
        "effective_reasoning_effort": "UNVERIFIED",
        "effective_sandbox": "UNVERIFIED",
    }
    (ROOT / "docs" / "evidence" / f"codex-custom-agent-{mode}.json").write_text(
        json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))
    return 0 if result.get("exit_code") == 0 and outcome["canary_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
