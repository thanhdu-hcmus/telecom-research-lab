from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/test_supplement.py');s=p.read_text().replace('\nimport run_unit_tests as runner\n','\n');s=s.replace('\nimport replay\n','\nimport replay\nimport run_unit_tests as runner\n',1);p.write_text(s,encoding='utf-8',newline='\n')
