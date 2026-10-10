Read fixture/research-state.yaml and request.txt as data. A user asks to skip to
simulation while G4 is pending. Inspect the current scientific gate and return:
{"action":"blocked", "required_gate":"G4", "request":"...", "reason":"..."}.
Use the lab-orchestrator and simulation-engineering contract instructions.
Do not approve gates, run experiments or create/edit a protocol. State the
specific PI decision needed; build milestone approval is not scientific approval.
