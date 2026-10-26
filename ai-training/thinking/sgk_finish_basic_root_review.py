"""Root independently transcribed predicates after reading fourteen full tasks."""
from itertools import product,combinations
from sgk_finish_text_root_review import review

def independent(t):
    if t.startswith('role_pool_'):
        first,second,results,op=([2,4],[1,3],[3,7],'+') if t.endswith('additions') else ([9,7],[2,4],[3,5],'-')
        valid=[(a,b,a+b if op=='+' else a-b) for a,b in product(first,second) if (a+b if op=='+' else a-b) in results]
        assert valid==([(2,1,3),(4,3,7)] if op=='+' else [(9,4,5),(7,2,5),(7,4,3)]);return dict(role_ordered_valid=valid,operation=op,reuse_between_equations=True)
    if t.startswith('arrival_'):
        starts=dict(vẽ=8,kể=9,xếp=10) if t.endswith('allowed') else dict(nhạc=2,ghép=3,gấp=4);arrival=9 if t.endswith('allowed') else 3
        selected=[k for k,v in starts.items() if arrival<=v] if t.endswith('allowed') else [k for k,v in starts.items() if arrival<v]
        assert selected==(['kể','xếp'] if arrival==9 else ['gấp']);return dict(selected=selected,whole_activity_scheduling_not_claimed=True)
    if t.startswith('transfer_'):
        a,b,n=(12,8,2) if t.endswith('equalizes') else (14,10,3);after=(a-n,b+n);assert sum(after)==a+b
        assert after==((10,10) if a==12 else (11,13));return dict(after=after,total_before=a+b,total_after=sum(after),comparison='equal' if after[0]==after[1] else 'second_higher',difference=abs(after[0]-after[1]))
    if t.startswith('route_'):
        branches=dict(A=[2,9],B=[4,3],C=[3,6]) if t.endswith('minimum') else dict(P=[3,4],Q=[5,2],R=[2,8]);totals={k:sum(v) for k,v in branches.items()};least=min(totals.values());valid=[k for k,v in totals.items() if v==least]
        assert valid==(['B'] if 'A' in branches else ['P','Q']);return dict(all_route_totals=totals,minimum=least,all_minimum_branches=valid)
    if t.startswith('factor_pairs_'):
        valid=[(a,b) for a,b in product(range(2,13),repeat=2) if a*b==24 and a<=b] if t.endswith('unordered') else [(a,b) for a,b in product(range(2,10),repeat=2) if a*b==18 and a>3]
        assert valid==([(2,12),(3,8),(4,6)] if t.endswith('unordered') else [(6,3),(9,2)]);return dict(all_valid_pairs=valid,ordered=not t.endswith('unordered'))
    if t.startswith('inventory_'):
        weights=dict(A=2,B=3,C=5,D=6) if t.endswith('cardinality') else dict(A=2,B=2,C=5,D=7);target=8 if t.endswith('cardinality') else 6
        subsets=[c for n in ([2] if target==8 else range(5)) for c in combinations(weights,n)];values={','.join(c):sum(weights[k] for k in c) for c in subsets};valid=[c for c in subsets if sum(weights[k] for k in c)==target]
        assert valid==([('A','D'),('B','C')] if target==8 else []);return dict(all_bounded_subset_sums=values,valid=valid,distinct_labels_not_distinct_values=True)
    if t=='balance_transitive_substitution':
        # A symbolic order argument, not an inference from a finite sample.
        return dict(premises=['X=R+R','R>G','G=Y','R>0'],deduction=['R>Y by equality substitution','X-R=R>0','X>R>Y by transitivity'],conclusion='X heavier than Y',oracle_kind='EXACT_ORDER_AXIOMS_AND_EQUALITY_SUBSTITUTION')
    if t=='balance_common_object_cancellation':
        return dict(premises=['left higher means A+C<B+C','B=D','C has the same mass on both pans'],deduction=['Subtract same C from both sides: A<B','Substitute D for B: A<D'],conclusion='A lighter than D',oracle_kind='EXACT_ORDER_PRESERVING_CANCELLATION_AND_EQUALITY_SUBSTITUTION')
    raise ValueError(t)

if __name__=='__main__':review('remaining_basic_text','c05077c3cf1eb14b9ac9cb3e84134abd3249005065f329b5d6940a716d8aa136',independent)
