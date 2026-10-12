from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/independent.py');s=p.read_text();a=s.index('def check_row(')
helper='''def check_candidate_flags(raw, computed, inputs, row_id, audit):
    """Check serialized diagnostics and independently recomputed predicates separately.

    Only binary64 roundoff can explain a diagnostic sign disagreement. This is
    not a feasibility certificate or a change to the approved rate tolerance.
    """
    stored = [number(raw["candidate_" + k]) for k in ("rw", "rs")]
    actual = [computed[k] for k in ("rw", "rs")]
    targets = inputs[3:]
    predicates = (
        ("candidate_constraints_pass", lambda r: all(x >= q for x, q in zip(r, targets))),
        ("candidate_within_rate_tolerance", lambda r: all(x >= q - RATE for x, q in zip(r, targets))),
        ("candidate_violation", lambda r: min(x - q for x, q in zip(r, targets)) < -RATE),
    )
    for field, predicate in predicates:
        reported = boolean(raw[field])
        expected_serialized = predicate(stored)
        expected_independent = predicate(actual)
        audit.eq(field, reported, expected_serialized, row_id)
        if expected_serialized != expected_independent:
            # Engineering roundoff in each rate, distinct from a scientific band.
            roundoff_only = all(
                math.isfinite(x) and abs(x - y) <= 64 * math.ulp(max(1.0, abs(x), abs(y), abs(q)))
                for x, y, q in zip(stored, actual, targets)
            )
            if roundoff_only:
                audit.diagnostic(field + ".roundoff", float(expected_serialized), float(expected_independent), row_id)
            else:
                audit.error(field + ".independent", reported, expected_independent, row_id)


'''
s=s[:a]+helper+s[a:];a=s.index('        audit.eq(\n            "candidate_constraints_pass",',s.index('    candidate = number(raw["candidate_a"])'));b=s.index('    else:\n        for k in (',a)
s=s[:a]+'        check_candidate_flags(raw, cr, inputs, row_id, audit)\n'+s[b:]
a=s.index('        pass_exact = rd["rw"]');b=s.index('        audit.eq("numeric_domain"',a);s=s[:a]+s[b:];p.write_text(s,encoding='utf-8',newline='\n')
p=Path('projects/m11-noma-qos/analysis/supplement/replay.py');s=p.read_text()
s=s.replace('    not_established = dict.fromkeys(("independent", "base", "tighter"), 0)','    not_established = dict.fromkeys(("independent", "base", "tighter"), 0)\n    not_applicable = dict.fromkeys(("independent", "base", "tighter"), 0)')
s=s.replace('        if not left["established"] or not right["established"]:\n            count["optimality_not_established"] += 1','        if any(x["status"] != "infeasible" and not x["established"] for x in (left, right)):\n            count["optimality_not_established"] += 1')
s=s.replace('        evidence = dict(\n            analytic=', '        not_applicable["independent"] += int(independent["status"] == "infeasible")\n        evidence = dict(\n            analytic=')
s=s.replace('            not_established[kind] += int(not established)','            not_established[kind] += int(status != "infeasible" and not established)\n            not_applicable[kind] += int(status == "infeasible")')
s=s.replace('        optimality_not_established_counts=not_established,','        optimality_not_established_counts=not_established,\n        optimality_not_applicable_counts=not_applicable,');p.write_text(s,encoding='utf-8',newline='\n')
