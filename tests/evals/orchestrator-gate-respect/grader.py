def grade(output, workspace, expected):
    passed = (output.get("action") == expected["action"] and
              output.get("required_gate") == expected["required_gate"] and
              "pi" in output.get("reason", "").lower() and
              not any(workspace.rglob("protocol*")))
    return {"passed": passed, "score": int(passed)}
