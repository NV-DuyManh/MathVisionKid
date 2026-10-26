"""Finite first expansion. Each logical domain completes before its next tier."""
import argparse
from exhaustive_primary_math import run,build_views,update_state,dumps
STAGE=[(op,n,prev) for n,prev in [(10,-1),(20,10),(100,20),(1000,100)] for op in ('+','-','/','invalid_division')]
STAGE.insert(4,('*',10,-1))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=3);p.add_argument('--through',type=int,default=1000);p.add_argument('--views',action='store_true');args=p.parse_args()
 for op,n,prev in STAGE:
  if n>args.through:continue
  print(dumps({'starting_domain_operation':op,'maximum':n,'previous':prev}),flush=True)
  run(op,n,prev,workers=args.workers,width=25)
 if args.views:build_views()
 s=update_state();print(dumps({'stage_complete':True,'maximum':args.through,'new_corpus':s['new_generated_cases'],'new_chat_rows':s['new_materialized_chat_rows']}),flush=True)
