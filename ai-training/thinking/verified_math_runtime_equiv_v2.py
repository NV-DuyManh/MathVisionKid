"""Post-hoc formula equivalence, with the original raw question contract intact."""
from verified_math_equivalence_v2 import equivalent
from verified_math_data_v2 import evaluate_expression
from verified_math_training_v2 import parse_output
from verified_math_runtime_v2 import inspect_problem,solve_verified
from verified_math_tutoring_v2 import wordproblem_tutor

def solve_equivalent_verified(problem,candidate,grade=None):
    try:
        plan=parse_output(candidate) if isinstance(candidate,str) else candidate
        if type(plan) is not dict or set(plan)!={'status','expr','unit'}:raise ValueError('BAD_SCHEMA')
        contract=inspect_problem(problem,grade)
        if contract['status']!='solve':return solve_verified(problem,plan,grade)
        if plan['status']!='solve' or type(plan['unit']) is not str or plan['unit']!=contract['unit']:raise ValueError('STATUS_OR_UNIT_MISMATCH')
        # Validate both concrete domains before any symbolic cancellation.
        proposed=evaluate_expression(plan['expr'],contract['facts'])
        reference=evaluate_expression(contract['expr'],contract['facts'])
        if not equivalent(plan['expr'],contract['expr'],[f['id'] for f in contract['facts']]):raise ValueError('SYMBOLIC_PLAN_NOT_EQUIVALENT')
        if proposed!=reference:raise ValueError('NUMERIC_CROSSCHECK_FAILED')
        result=solve_verified(problem,{'status':'solve','expr':contract['expr'],'unit':contract['unit']},grade)
        if result['accepted']:
            result.update(symbolic_equivalence_verified=True,candidate_expression=plan['expr'],
                          verification='RAW_FULL_TEMPLATE_CONTRACT_AND_SYMBOLIC_IDENTITY_AND_EXACT_FRACTION')
        return result
    except (ValueError,TypeError,KeyError,SyntaxError,ZeroDivisionError,RecursionError) as e:
        return {'accepted':False,'status':'verification_failed','answer':None,'reason':str(e)}

def tutor_equivalent_verified(problem,candidate,grade,mode='hint',step_index=0):
    result=solve_equivalent_verified(problem,candidate,grade)
    if not result.get('accepted') or result['status']!='solved':
        return wordproblem_tutor(problem,candidate,grade,mode,step_index)
    approved={'status':'solve','expr':result['expression'],'unit':result['unit']}
    tutoring=wordproblem_tutor(problem,approved,grade,mode,step_index)
    tutoring['machine']['symbolic_equivalence_verified']=True
    # Keep numerical answers/whole plans out of the default hint payload.
    return tutoring
