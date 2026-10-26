from pathlib import Path
p=Path('thinking/sgk_completion_union_recipe.py');s=p.read_text('utf8')
s=s.replace("RUN=HERE/'cloud_publication/sgk_completion_20261021'","RUN=HERE/'cloud_publication/sgk_final_gaps_20261021'")
s=s.replace("('sgk_completion_20261021',36,144)]","('sgk_completion_20261021',36,144),('sgk_final_gaps_20261021',71,284)]")
s=s.replace('EXPECTED_ARTIFACTS=35','EXPECTED_ARTIFACTS=36').replace('EXPECTED_CHAT_MEMBERS=29','EXPECTED_CHAT_MEMBERS=30')
s=s.replace('6501780','6502064').replace('6501828','6502112')
s=s.replace("len(refs)!=4","len(refs)!=5").replace("for r in refs})!=4","for r in refs})!=5")
s=s.replace("!=184","!=255").replace("!=736","!=1020").replace("=184","=255").replace("=736","=1020")
s=s.replace("four_reviewed_appends","five_reviewed_appends").replace("all35","all36").replace("four distinct","five distinct").replace("35/29","36/30").replace("184/736","255/1020").replace("four reviewed","five reviewed").replace("RUN5's","RUN7's").replace("AFTER RUN5","AFTER RUN7")
Path('thinking/sgk_final_gaps_union_recipe.py').write_text(s,encoding='utf8')
print('staged five-append full data-only union helper')

