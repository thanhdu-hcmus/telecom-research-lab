from pathlib import Path

r=Path.cwd()
step=(r/'.cache/run_p6_canonical_step.py').read_text(encoding='utf-8')
step=step.replace("marker=repo/f'.cache/p6-canonical-{kind}-active.json'", "marker=repo/f'.cache/p6-canonical-attempt2-{kind}-active.json'")
step=step.replace("repo/'.cache/p6-canonical'/", "repo/'.cache/p6-canonical-attempt2'/")
step=step.replace("record=dict(status='RUNNING',kind=kind,", "record=dict(status='RUNNING',attempt=2,review_round=5,kind=kind,")
step=step.replace("assert ready['recommendation']=='ready' and ready['enforced_independent_review']", "assert ready['recommendation']=='ready' and ready['enforced_independent_review'] and ready['review_round']==5")
(r/'.cache/run_p6_canonical_attempt2_step.py').write_text(step,encoding='utf-8',newline='\n')
watch=(r/'.cache/finish_p6_canonical_assessment.py').read_text(encoding='utf-8')
watch=watch.replace('p6-canonical-assessment-active','p6-canonical-attempt2-assessment-active').replace("repo/'.cache/p6-canonical'/", "repo/'.cache/p6-canonical-attempt2'/").replace('p6-canonical-{kind}-active','p6-canonical-attempt2-{kind}-active')
watch=watch.replace("record=dict(status='WAITING',", "record=dict(status='WAITING',attempt=2,review_round=5,")
(r/'.cache/finish_p6_canonical_attempt2_assessment.py').write_text(watch,encoding='utf-8',newline='\n')
print('Prepared new versioned attempt2 control helpers. No canonical operation launched.')
