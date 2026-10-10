"""Extract only probe metadata from local Codex rollouts, never whole chats."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from probe_environment import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    events = [json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines()]
    parent = next(e["thread_id"] for e in events if e.get("type") == "thread.started")
    rollouts = Path.home() / ".codex" / "sessions"
    found = {"parent_thread_id": parent, "children": []}
    for path in rollouts.rglob("*.jsonl"):
        with path.open(encoding="utf-8") as handle:
            first = handle.readline()
            try:
                first_event = json.loads(first)
            except (ValueError, json.JSONDecodeError):
                continue
            if first_event.get("type") != "session_meta":
                continue
            metadata = first_event.get("payload", {})
            source = metadata.get("source", {})
            spawn = (
                source.get("subagent", {}).get("thread_spawn", {})
                if isinstance(source, dict)
                else {}
            )
            is_parent = metadata.get("id") == parent
            is_child = spawn.get("parent_thread_id") == parent
            if not (is_parent or is_child):
                continue
            summary = {
                "thread_id": metadata.get("id"),
                "role": metadata.get("agent_role"),
                "spawn": spawn,
                "runtime": [],
                "scope_fixture_in_skill_catalog": False,
            }
            for line in handle:
                event = json.loads(line)
                payload = event.get("payload", {})
                if event.get("type") == "turn_context":
                    summary["runtime"].append(
                        {
                            key: payload.get(key)
                            for key in ["model", "effort", "sandbox_policy", "approval_policy"]
                        }
                    )
                if event.get("type") == "response_item" and payload.get("role") == "developer":
                    text = "\n".join(item.get("text", "") for item in payload.get("content", []))
                    # Do not infer skill visibility from a user mention or tool read.
                    summary["scope_fixture_in_skill_catalog"] |= (
                        "## Skills" in text and "- m0-scope-canary:" in text
                    )
            if is_parent:
                found["parent"] = summary
            else:
                found["children"].append(summary)
    roles = [child for child in found["children"] if child["role"] == "m0_probe"]
    found["custom_role_spawn"] = "PASS" if len(roles) == 1 else "UNVERIFIED"
    if roles and roles[0]["runtime"]:
        runtime = roles[0]["runtime"][0]
        found["requested_effort"] = "medium"
        found["observed_effort"] = runtime["effort"]
        found["effort_override"] = "PASS" if runtime["effort"] == "medium" else "FAIL"
        found["requested_sandbox"] = "read-only"
        found["observed_sandbox"] = runtime["sandbox_policy"].get("type")
        found["sandbox_override"] = "PASS" if found["observed_sandbox"] == "read-only" else "FAIL"
        parent_catalog = found.get("parent", {}).get("scope_fixture_in_skill_catalog")
        child_catalog = roles[0]["scope_fixture_in_skill_catalog"]
        found["per_agent_skill_disable"] = (
            "FAIL"
            if parent_catalog and child_catalog
            else "PASS"
            if parent_catalog
            else "UNVERIFIED"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(found, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in found.items() if k not in {"children", "parent"}}, indent=2))
    return 0 if found["custom_role_spawn"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
