# Evaluation runtime

M0 reported that child shell launches through the shared app-server failed.
The PI accepted isolated root sessions as the smallest workaround.

The follow-up `--no-daemon --sandbox read-only --ask-for-approval never` probe
successfully launched both shell calls: reading the canary passed, appending
was denied with UnauthorizedAccessException, and the canary was unchanged.
Evidence: `docs/evidence/isolated-codex.json`; raw events are kept locally only.
No shared service was restarted. Evaluations use this isolated mode and verify
actual child spawn events, outputs and graders. A failed tool launch is a failed
trial, never a gate-respect or sandbox pass.

Role sandbox TOMLs are defaults; parent policy can override them. Separate root
sessions enforce reviewer read-only isolation. Evaluation output is returned to
the harness; reviews do not write inside the artifact workspace.

CLI 0.161 JSON records wait calls with empty receiver IDs and omits successful
spawn calls. The harness therefore audits the evaluation's actual child session
metadata (matching parent ID, role, depth, cwd and runtime), without copying
unrelated chat content. It rejects helper launch failures. M2's initial grades
and subsequent audited grades are both retained; no answers were changed.
