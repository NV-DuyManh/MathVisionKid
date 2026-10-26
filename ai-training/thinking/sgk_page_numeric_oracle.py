"""Independent finite structure oracles for original G4 page supplement.

Does not read sealed challenge, eval, or pilot payloads. It tests source givens,
not a target-answer rewrite, and records exact source line hashes.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext
from itertools import permutations, product
import ast, hashlib, json, re

RUN=Path(__file__).resolve().parent/'cloud_publication/sgk_page_audit_20261019'

def calc(expr,decimal=False):
    def walk(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            v=ast.get_source_segment(expr,n)
            return Decimal(v) if decimal else Fraction(v)
        if isinstance(n,ast.UnaryOp):
            assert isinstance(n.op,(ast.UAdd,ast.USub))
            return -walk(n.operand) if isinstance(n.op,ast.USub) else walk(n.operand)
        assert isinstance(n,ast.BinOp)
        a,b=walk(n.left),walk(n.right)
        if isinstance(n.op,ast.Add):return a+b
        if isinstance(n.op,ast.Sub):return a-b
        if isinstance(n.op,ast.Mult):return a*b
        if isinstance(n.op,ast.Div):return a/b
        raise AssertionError('unsupported expression')
    with localcontext() as c:c.prec=95;return walk(ast.parse(expr,mode='eval').body)

def audit(r):
    o=r['oracle_evidence'];kind=o['kind'];evidence={}
    if kind=='abacus':
        vals=[]
        # Enumerate numeric values, independently extract their four digits.
        for n in range(10000):
            ds=list(map(int,f'{n:04d}'))
            if sum(ds)==o['total']:vals.append(n)
        optimum=(max if o['want']=='lớn nhất' else min)(vals)
        assert o['value']==optimum
        assert list(map(int,f'{optimum:04d}'))==o['digits']
        evidence=dict(valid_allocations=len(vals),optimum=optimum)
    elif kind=='successor':
        assert o['answer']>o['n']>=0 and o['answer']-o['n']==1
        evidence=dict(successor=o['answer'],strictly_greater=True)
    elif kind=='bounded_natural':
        assert o['answer']==max(range(10**o['digits']))
        evidence=dict(maximum=o['answer'])
    elif kind=='delete':
        text=o['text']; options={i+1:int(text[:i]+text[i+1:]) for i in range(len(text)) if (text[:i]+text[i+1:])[0]!='0'}
        optimum=(min if o['want']=='nhỏ nhất' else max)(options.values())
        assert o['result']==optimum
        assert o['positions']==[i for i,n in options.items() if n==optimum]
        evidence=dict(valid_deletions=options)
    elif kind=='digit_inequality':
        values={d:int(o['template'].replace('A',str(d))) for d in range(10)}
        valid=[d for d,n in values.items() if n<o['bound']] if o['rel']=='<' else [d for d,n in values.items() if n>o['bound']]
        assert valid==o['digits'];evidence=dict(all_values=values,valid=valid)
    elif kind=='global_cards':
        valid=[]
        for a,b in product(o['cards'],repeat=2):
            if a!=b and o['left0']*10+a<o['right0'] and o['left1']*10+b>o['right1']:valid.append([a,b])
        assert sorted(valid)==sorted(o['pairs']);evidence=dict(valid_pairs=valid)
    elif kind=='columns':
        pattern, rhs=o['puzzle'].split(' = ')
        valid=[]
        for a in range(10):
            for b in range(10):
                expression=pattern.replace('A',str(a)).replace('B',str(b)).replace('−','-')
                tokens=re.findall(r'\d+',expression)
                if any(len(s)>1 and s[0]=='0' for s in tokens):continue
                if calc(expression)==Fraction(rhs):valid.append([a,b])
        assert valid==o['pairs'];evidence=dict(all_satisfying_pairs=valid,assignments_examined=100)
    elif kind=='swap':
        s=list(o['start']);target=o['target']
        for i,j in o['route']:
            assert i!=j and 1<=i<=len(s) and 1<=j<=len(s)
            s[i-1],s[j-1]=s[j-1],s[i-1]
        assert ''.join(s)==target
        # Independent minimum: permutation cycles, no search from builder.
        visited=set();cycles=[]
        dest={ch:i for i,ch in enumerate(target)}
        for i in range(len(s)):
            if i in visited:continue
            cyc=[];j=i
            while j not in visited:
                visited.add(j);cyc.append(j+1);j=dest[o['start'][j]]
            cycles.append(cyc)
        minimum=sum(len(c)-1 for c in cycles)
        assert minimum==o['minimum']==len(o['route'])
        evidence=dict(position_cycles=cycles,independent_minimum=minimum,route_reaches_target=True)
    elif kind=='insert_plus':
        valid=[];s=o['digits'];evaluations=[]
        for i in range(1,len(s)):
            if s[0]=='0' or s[i]=='0':continue
            value=Fraction(s[:i])+Fraction(s[i:]);evaluations.append([i,str(value)])
            if value==o['total']:valid.append(i)
        assert valid==o['cuts'];evidence=dict(every_cut=evaluations,valid_cuts=valid)
    elif kind=='prefix':
        n=o['n'];d=o['digits'];assert 10**(d-1)<=n<10**d
        combined=int(str(o['prefix'])+str(n))
        assert combined==o['new'] and combined-n==o['difference']==o['prefix']*10**d
        evidence=dict(concatenated=combined,place_value_difference=combined-n)
    elif kind=='round_place':
        # Neighbor-distance oracle, independent of the builder half-up formula.
        outputs={}
        for p in o['places']:
            q,remainder=divmod(o['n'],p)
            lower=q*p;upper=lower+p
            outputs[p]=lower if remainder<p-remainder else upper
        valid=[p for p in o['places'] if outputs[p]==o['out']]
        assert valid==o['valid'];evidence=dict(outputs=outputs,valid_places=valid)
    elif kind=='unit_pairs':
        f=Fraction(o['fraction']);p,q=f.numerator,f.denominator
        pairs=[]
        # (p*a-q)(p*b-q)=q^2: enumerate divisors, no small-a bound.
        for u in range(1,q*q+1):
            if q*q%u:continue
            v=q*q//u
            if (u+q)%p or (v+q)%p:continue
            a,b=(u+q)//p,(v+q)//p
            if 0<a<b and Fraction(1,a)+Fraction(1,b)==f:pairs.append([a,b])
        assert sorted(pairs)==sorted(o['pairs']);evidence=dict(divisor_factorization_pairs=pairs)
    elif kind=='integrality':
        values=[Fraction(o['count'])*Fraction(f) for f in o['fractions']]
        possible=[v.denominator==1 and 0<=v<=o['count'] for v in values]
        assert list(map(str,values))==o['values'] and possible==o['possible']
        evidence=dict(exact_required_counts=list(map(str,values)),possible=possible,actual_event_not_inferred=True)
    elif kind=='parameter':
        values=[calc(e) for e in o['expressions']]
        assert list(map(str,values))==o['values']
        assert [m for m,v in zip(o['domain'],values) if v==max(values)]==o['args']
        evidence=dict(exact_values=list(map(str,values)))
    elif kind=='structural_arithmetic':
        assert calc(o['expression'])==Fraction(o['value'])
        evidence=dict(exact_value=str(calc(o['expression'])))
    elif kind=='reverse_error':
        matches=[n for n in range(o['wrong']+1) if sum(int(d)*n for d in str(o['multiplier']))==o['wrong']]
        assert matches==[o['x']] and o['x']*o['multiplier']==o['correct']
        evidence=dict(independent_recovery=matches,correct_product=o['correct'])
    elif kind=='numeral_filter':
        variant=o['variant'];valid=[];detail=[]
        for n in o['numbers']:
            digits=list(map(int,f'{n:09d}'))
            checks=([digits[-5]==2,digits[-2]==0,digits[-1] in (0,2,4,6,8)] if variant=='thousands_and_parity' else
                    [digits[-6:-3]==[0,4,2],digits[-1]==5] if variant=='class_pattern' else
                    [digits[-4]==5,digits[-3]==0,digits[-1] in (0,2,4,6,8)])
            if all(checks):valid.append(n)
            detail.append(dict(n=n,conditions=checks))
        assert valid==o['result'];evidence=dict(per_card_checks=detail,valid=valid)
    else:raise AssertionError(kind)
    numeric=[]
    for s in r['worked_steps']:
        e=s.get('expression')
        if not e:continue
        exact=calc(e);assert exact==Fraction(s['result'])
        dec=calc(e,True)
        with localcontext() as ctx:
            ctx.prec=95;expected=Decimal(exact.numerator)/Decimal(exact.denominator)
            assert abs(dec-expected)<Decimal('1e-80')
        numeric.append(dict(step_id=s['step_id'],expression=e,exact=str(exact),decimal_95_digits_agrees=True))
    return dict(structural_oracle=evidence,numeric_steps=numeric)

def main():
    path=RUN/'root_numeric/draft_cases.jsonl'
    reports=[]
    for line in path.read_bytes().splitlines():
        r=json.loads(line)
        reports.append(dict(sample_id=r['sample_id'],source_row_sha256=hashlib.sha256(line).hexdigest(),status='PASS',**audit(r)))
    assert len(reports)==48
    dest=RUN/'root_numeric/independent_oracles.jsonl'
    dest.write_bytes(b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for r in reports))
    print(json.dumps(dict(rows=len(reports),numeric_steps=sum(len(r['numeric_steps']) for r in reports),status='PASS',sha256=hashlib.sha256(dest.read_bytes()).hexdigest())))

if __name__=='__main__':main()
