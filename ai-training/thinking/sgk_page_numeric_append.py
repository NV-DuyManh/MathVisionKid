"""Original, bounded numeric representation drafts from actual G4 page audit.

Only creates new staging files. Acceptance requires later semantic cross-review.
"""
from pathlib import Path
from fractions import Fraction
from itertools import product, permutations, combinations
from collections import deque
import ast, hashlib, json
import exhaustive_colab_loader as L
from sgk_gap_release import evaluate

ROOT=Path(__file__).resolve().parent
RUN=ROOT/'cloud_publication/sgk_page_audit_20261019'
OUT=RUN/'root_numeric'
ROWS=[]

def st(title,reason,result,expression=None,unit='',explanation=None):
    return dict(title=title,reason=reason,result=str(result),expression=expression,unit=unit,explanation=explanation or reason)

def ans(result,unit='',quantity='Kết quả'):
    return dict(quantity=quantity,result=str(result),unit=unit)

# Nearest sources locate partial analogues, not proofs that all representations
# were already covered. Full-field comparison is recorded separately.
FAMILIES={
 'abacus_budget':('g4v1',[49],'natural_numbers_millions','Fixed total rings, at most nine per place, extremize position weights.', ['primary_20261018_finish_g4_millions_place_value_compose_inventory']),
 'unbounded_naturals':('g4v1',[50],'natural_numbers_millions','Construct a successor to refute a largest natural number.', ['primary_20261018_g4_numbers_0049_successors_across_millions_and_parity']),
 'delete_one_digit':('g4v1',[51,81],'natural_numbers_millions','Delete one position while preserving all other order.', ['sgk_g12_20261019_one_digit_swap_repair_01']),
 'digit_inequality':('g4v1',[52],'compare_round_naturals','Find all digits satisfying strict comparison of whole numerals.', ['primary_20261018_old_g1_compare_0097_select_card_to_satisfy_strict_inequality']),
 'global_card_assignment':('g4v1',[55],'compare_round_naturals','Shared finite card inventory couples simultaneous comparisons.', ['sgk_gap_20261019_g4_parity_cards_three_digit_odd']),
 'column_multi_blank':('g4v1',[78,81],'addition_subtraction_many_digits','Interdependent missing columns including carry or exchange.', ['sgk_g12_20261019_blank_digit_column_constraints_01','sgk_g12_20261019_blank_digit_column_constraints_04']),
 'minimum_pair_swaps':('g4v1',[89],'natural_numbers_millions','Shortest sequence of arbitrary pair swaps to a specified order.', ['sgk_g12_20261019_one_digit_swap_repair_01']),
 'insert_single_plus':('g4v1',[90],'addition_subtraction_many_digits','Choose a cut in an ordered digit string; no reordering.', ['sgk_gap_20261019_g3_expression_choice_insert_bracket']),
 'prefix_difference':('g4v1',[115],'natural_numbers_millions','Prepending a fixed place contribution leaves an invariant difference.', ['primary_20261018_finish_g4_millions_place_value_zero_placeholder']),
 'infer_rounding_place':('g4v1',[117],'compare_round_naturals','Infer every possible rounding place from input and output.', ['sgk_gap_20261019_g4_rounding_preimage_all_integers']),
 'unit_fraction_decomposition':('g4v2',[110],'fraction_operations','Decompose into two distinct positive unit fractions; prove completeness.', ['primary_20261018_g4_fraction_concepts_0056_equivalent_partition_eighths_twelfths']),
 'discrete_fraction_integrality':('g4v2',[101],'fraction_operations','A fraction of an indivisible finite count must be integral.', ['primary_20261018_g4_practice_experience_0094_equal_card_fraction_colouring_plan_compare']),
 'finite_parameter_extrema':('g4v1',[17],'expressions_letters_properties','Finite parameter domain and nonzero denominator, then compare values.', ['primary_20261018_finish_g4_letter_expression_rectangle_variable']),
 'structural_product_cancel':('g4v2',[61,69,100,109],'fraction_operations','Identify matching factors before multiplying; do not cancel summands.', ['primary_20261018_finish_g4_all_fraction_operations_multiply_divide_contrast']),
 'reverse_algorithm_error':('g4v2',[22],'multiply_divide_two_digits','Recover operand from an explicitly supplied incorrect partial-product rule.', ['primary_20261018_g4_muldiv_0052_two_digit_partial_products']),
 'conjunctive_numeral_filter':('g4v1',[39,40,44,54],'natural_numbers_millions','Conjunction of class, position and parity conditions, not one filter.', ['primary_20261018_finish_g4_millions_place_value_contrast_same_digit'])
}

def add(family,variant,problem,request,hints,steps,answers,oracle,student=None,can_solve=True):
    book,pages,node,why,near=FAMILIES[family]
    sid=f'sgk_page_20261019_g4_{family}_{variant}'
    for i,s in enumerate(steps):s['step_id']=f's{i}'
    hs=[dict(level=i+1,hint=h,question=q) for i,(h,q) in enumerate(hints)]
    row=dict(sample_id=sid,case_group_id=sid,split='train',grade=4,topic=family,
      problem=problem,givens=[dict(id='g0',text=problem,value=None,unit='',role='EXPLICIT_TEXT_AS_SUPPLIED')],
      requested_quantity=request,student_work=dict(text=student,origin='EXPLICIT_HYPOTHETICAL_STUDENT_WORK') if student else None,
      initial_guidance=[hs[0]['hint']],hints=hs,worked_steps=steps,expected_answer=answers,can_solve=can_solve,
      case_kind='guard' if not can_solve else 'misconception' if student else 'supplementary',
      curriculum_assignment=dict(node_id='current_g4_'+node,book_id=book,printed_pages=pages,
       mapping_status='ORIGINAL_SUBREPRESENTATION_AFTER_ACTUAL_PAGE_REVIEW',curriculum_scope='CURRENT_KNTT_TOPIC_WITH_REASONING_ENRICHMENT'),
      acceptance_status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',quality_status='DRAFT',
      human_verified=False,teacher_certified=False,owner_human_reviewed=False,
      provenance=dict(authoring_method='original_AI_teacher',authorship_origin='AI_ORIGINAL_NEW_PEDAGOGIC_CASE',
       source_role='AI_GENERATED',human_verified=False,teacher_certified=False,owner_human_reviewed=False,
       independent_external_review=False,acceptance_basis='OWNER_PREAUTHORIZATION_AFTER_SEVEN_CRITERION_QA_PENDING',
       real_physical_observation_claimed=False,textbook_exercise_copied=False),
      coverage=dict(kind='ACTUAL_PAGE_REPRESENTATION_GAP_APPEND',old_source_changed=False,text_only_not_vision_training=True),
      canonical_case=dict(family=family,operations=[s['expression'] for s in steps if s.get('expression')],numeric_values=[]),
      oracle_evidence=oracle)
    ROWS.append(row)

def hs(a,b,c):
    return [(a,'Em cần giữ những điều kiện nào?'),(b,'Em áp dụng cho từng vị trí hoặc trường hợp ra sao?'),(c,'Em kiểm tính đúng và đầy đủ bằng cách nào?')]

def author():
    # Ring budgets use finite place weights, not a supplied inventory of values.
    for variant,total,ncols,want in [('largest',11,4,'lớn nhất'),('smallest',13,4,'nhỏ nhất')]:
        valid=[ds for ds in product(range(10),repeat=ncols) if sum(ds)==total]
        val=lambda ds:sum(d*10**(ncols-1-i) for i,d in enumerate(ds))
        chosen=(max if want=='lớn nhất' else min)(valid,key=val);value=val(chosen)
        add('abacus_budget',variant,f'Bàn tính giả định có bốn cột nghìn, trăm, chục, đơn vị. Dùng hết {total} vòng; mỗi cột có từ 0 đến 9 vòng, cột trống chỉ 0. Một vòng ở cột nào biểu thị một đơn vị của hàng đó. Lập giá trị {want}. Không bắt buộc giá trị có bốn chữ số.',f'Giá trị {want} và số vòng từng cột',
          hs('Một vòng có giá trị tùy cột; tổng số vòng được giữ nguyên.','Ưu tiên cột có trọng số phù hợp với yêu cầu, nhưng không cột nào vượt sức chứa.','Kiểm số vòng, sức chứa và so việc chuyển một vòng giữa hai cột.'),
          [st('Chọn vị trí vòng','Chuyển một vòng sang cột cao hơn làm giá trị tăng; chuyển xuống làm giảm.',str(list(chosen)),explanation='Ưu tiên từ cột cao xuống cho lớn nhất, hoặc từ cột thấp lên cho nhỏ nhất; luôn dừng ở chín vòng mỗi cột.'),st('Đọc và kiểm','Ghép các hàng rồi đếm lại tổng vòng.',value,expression='+'.join(str(d*10**(3-i)) for i,d in enumerate(chosen)),explanation=f'Các cột lần lượt là {list(chosen)}; tổng số vòng bằng {total}. Mọi cách thay đổi làm giảm ưu tiên tại hàng cao nhất đang khác.')],
          [ans(value),ans(str(list(chosen)),quantity='Vòng theo nghìn, trăm, chục, đơn vị')],dict(kind='abacus',total=total,ncols=ncols,want=want,value=value,digits=chosen))
    add('abacus_budget','reject_overfull','Bàn tính có bốn cột nghìn, trăm, chục, đơn vị, mỗi cột tối đa 9 vòng. Phải dùng đủ 12 vòng. Bạn ghi: đặt cả 12 vòng ở cột nghìn là số lớn nhất. Nhận xét cách đặt và tìm giá trị lớn nhất hợp lệ. Không được đổi cấu tạo bàn tính.','Kiểm cách đặt và sửa',hs('Phân biệt tổng số vòng với sức chứa mỗi cột.','Sau khi cột ưu tiên đã đầy, xét cột có trọng số tiếp theo.','Đếm lại tất cả vòng và kiểm từng cột.'),[st('Kiểm luật','Mỗi cột chỉ chứa tối đa chín vòng.','Cách đặt đã cho không hợp lệ',explanation='Mười hai vòng trong một cột vượt sức chứa, dù tổng vòng không đổi.'),st('Phân bố hợp lệ','Giữ nhiều vòng nhất ở hàng cao, rồi đến hàng kế tiếp.','9,3,0,0',explanation='Chín vòng ở nghìn, ba ở trăm, không còn vòng cho hàng thấp.'),st('Tính giá trị','Cộng giá trị từng cột.',9300,'9*1000+3*100',explanation='Đủ mười hai vòng; chuyển một vòng xuống sẽ giảm giá trị.')],[ans(9300)],dict(kind='abacus',total=12,ncols=4,want='lớn nhất',value=9300,digits=[9,3,0,0]),student='đặt cả 12 vòng ở cột nghìn là số lớn nhất')

    for variant,cap in [('successor',99999999),('beyond_named_class',999999999)]:
        add('unbounded_naturals',variant,f'Một bạn cho rằng {cap} là số tự nhiên lớn nhất vì tất cả các chữ số đều là 9. Không giới hạn số chữ số được viết. Hãy đưa một số tự nhiên lớn hơn để kiểm lời khẳng định.','Một phản ví dụ và kết luận',hs('Các chữ số đã viết không phải là giới hạn của tập số tự nhiên.','Dùng quan hệ giữa một số tự nhiên và số liền sau nó.','So phản ví dụ với số được khẳng định là lớn nhất.'),[st('Lấy số liền sau','Thêm một vào một số tự nhiên vẫn được một số tự nhiên.',cap+1,f'{cap}+1',explanation='Qua mốc tăng số chữ số vẫn là số tự nhiên.'),st('Kiểm lời khẳng định','Chỉ một số tự nhiên lớn hơn đã đủ bác bỏ tính lớn nhất.','Không có số tự nhiên lớn nhất',explanation='Với bất cứ số tự nhiên nào cũng làm được cách lấy số liền sau này.')],[ans(cap+1,quantity='Phản ví dụ'),ans('Không có số tự nhiên lớn nhất',quantity='Kết luận')],dict(kind='successor',n=cap,answer=cap+1))
    add('unbounded_naturals','bounded_contrast','Hộp thẻ chỉ cho phép viết số tự nhiên có không quá ba chữ số, kể cả 0. Bạn nói: không có số tự nhiên lớn nhất nên cũng không có số lớn nhất trong hộp. Hãy phân biệt điều kiện hộp thẻ với toàn bộ số tự nhiên.','Số lớn nhất trong hộp và nhận xét',hs('Đọc xem bài có giới hạn số chữ số hay không.','So các chữ số từ hàng cao nhất trong miền đã giới hạn.','Phản ví dụ ngoài hộp có được dùng để bác kết luận trong hộp không?'),[st('Tìm trong miền hữu hạn','Mỗi hàng chỉ đến chín và chỉ có tối đa ba hàng.','999',explanation='Mọi số một hoặc hai chữ số nhỏ hơn số ba chữ số; trong ba chữ số, chọn chín ở từng hàng.'),st('Phân biệt miền','Số lớn hơn vẫn tồn tại trong toàn bộ số tự nhiên nhưng không thuộc hộp.','Hộp có lớn nhất; toàn bộ số tự nhiên thì không',explanation='Số một nghìn đã có bốn chữ số nên không phải phản ví dụ hợp lệ đối với hộp.')],[ans(999),ans('Không có số tự nhiên lớn nhất trong toàn bộ tập',quantity='Miền không giới hạn')],dict(kind='bounded_natural',digits=3,answer=999),student='không có số tự nhiên lớn nhất nên cũng không có số lớn nhất trong hộp')

    for variant,text,want in [('min','72534','nhỏ nhất'),('max','40865','lớn nhất'),('repeated_positions','66321','nhỏ nhất')]:
        possibilities=[(i,text[:i]+text[i+1:]) for i in range(len(text)) if (text[:i]+text[i+1:])[0]!='0']
        target=(min if want=='nhỏ nhất' else max)(int(s) for i,s in possibilities)
        deletions=[i+1 for i,s in possibilities if int(s)==target]
        add('delete_one_digit',variant,f'Từ dãy chữ số {text}, xóa đúng một chữ số. Giữ nguyên thứ tự các chữ số còn lại, không đảo hay thêm chữ số; số còn lại phải có bốn chữ số và không bắt đầu bằng 0. Tìm số {want} và tất cả vị trí có thể xóa để nhận nó. Đánh vị trí từ trái sang phải bắt đầu 1.','Số cần tìm và vị trí xóa',hs('Xóa một vị trí khác với đổi chỗ hai vị trí.','Liệt kê kết quả khi bỏ từng vị trí; loại số không đủ chữ số.','So giá trị cả số và giữ mọi vị trí cho cùng kết quả.'),[st('Xét đủ các vị trí','Mỗi kết quả hợp lệ phải đến từ một trong năm vị trí.', '; '.join(f'vị trí {i+1}: {s}' for i,s in possibilities),explanation='Chỉ bỏ ký tự ở vị trí đang xét, không sắp lại phần còn lại.'),st('Chọn và kiểm','So từ hàng cao nhất, giữ cả các vị trí cho cùng giá trị.',str(target),explanation=f'Các vị trí xóa phù hợp là {deletions}; thay ngược vào dãy ban đầu để kiểm đúng một lần xóa.')],[ans(target),ans(str(deletions),quantity='Vị trí xóa')],dict(kind='delete',text=text,want=want,result=target,positions=deletions))

    for variant,template,bound,rel in [('strict_low','4A26',4626,'<'),('strict_high','70A4',7054,'>'),('middle','2A58',2458,'<')]:
        ds=[d for d in range(10) if (int(template.replace('A',str(d)))<bound if rel=='<' else int(template.replace('A',str(d)))>bound)]
        add('digit_inequality',variant,f'A là một chữ số từ 0 đến 9. Tìm tất cả A để {template} {rel} {bound}. Các ký tự ghép thành một số tự nhiên theo hàng, không phải phép nhân. Dấu so sánh là nghiêm ngặt.','Tất cả chữ số A',hs('So hàng cao nhất có thể khác nhau trước; chú ý dấu nghiêm ngặt.','Nếu hàng chứa ô bằng hàng tương ứng, tiếp tục xét các hàng sau.','Thử cả chữ số biên để tránh nhận nhầm trường hợp bằng nhau.'),[st('Xét hàng quyết định','Các hàng trước ô giữ nguyên, nên so chữ số tại ô rồi xét phần đuôi khi bằng.',str(ds),explanation=f'Đổi A thành từng chữ số và so toàn bộ với {bound}; trường hợp bằng nhau không thỏa dấu {rel}.'),st('Kiểm đầy đủ','A chỉ có mười giá trị có thể thử.', '; '.join(f'{d}: {template.replace("A",str(d))}' for d in ds),explanation='Các chữ số ngoài danh sách đều cho quan hệ ngược hoặc bằng, không được bỏ qua việc xét phần đuôi.')],[ans(str(ds))],dict(kind='digit_inequality',template=template,bound=bound,rel=rel,digits=ds))

    # The inventory is shared across BOTH comparisons.
    for variant,cards,left0,right0,left1,right1 in [('all_assignments',[1,4,7],3,35,8,81),('larger_inventory',[0,2,5],4,43,6,60),('shared_constraint',[2,6,8],5,57,9,95)]:
        valid=[]
        for a,b in permutations(cards,2):
            if left0*10+a<right0 and left1*10+b>right1:valid.append([a,b])
        a_options=[d for d in cards if left0*10+d<right0];b_options=[d for d in cards if left1*10+d>right1]
        add('global_card_assignment',variant,f'Có đúng ba thẻ {cards}, mỗi thẻ chỉ có một bản. Dùng hai thẻ khác nhau điền A, B, còn một thẻ không dùng. Phải đồng thời đúng: {left0}A < {right0} và {left1}B > {right1}. Viết mọi cặp (A,B); chữ ghép thành số hai chữ số.','Tất cả cặp (A,B) dùng được',hs('Một thẻ dùng ở ô này không còn để dùng ở ô kia.','Kiểm từng quan hệ, rồi loại cặp dùng cùng một thẻ hai lần.','Đối chiếu cả hai phép so sánh và số thẻ đã dùng cho mỗi cặp.'),[st('Tách hai điều kiện','Mỗi ô phải thỏa phép so riêng trước khi xét kho thẻ chung.',f'A thuộc {a_options}; B thuộc {b_options}',explanation='Khi hàng chục bằng nhau, so chữ số hàng đơn vị; mỗi dấu là nghiêm ngặt.'),st('Ghép không lặp thẻ','Chọn có thứ tự hai thẻ khác nhau từ kho.',str(valid),explanation='Mỗi cặp đã kiểm cả hai dấu so; không dùng thêm thẻ từ ngoài kho và không dùng lại một bản.')],[ans(str(valid))],dict(kind='global_cards',cards=cards,left0=left0,right0=right0,left1=left1,right1=right1,pairs=valid))

    column_data=[('carry','3A7 + 2B6 = 663','add',[(3*100+a*10+7,2*100+b*10+6,a,b) for a in range(10) for b in range(10) if 3*100+a*10+7+2*100+b*10+6==663]),('exchange','8A2 − 3B7 = 425','sub',[(800+a*10+2,300+b*10+7,a,b) for a in range(10) for b in range(10) if 800+a*10+2-(300+b*10+7)==425]),('coupled','A48 + 3B7 = 725','add',[(a*100+48,300+b*10+7,a,b) for a in range(1,10) for b in range(10) if a*100+48+300+b*10+7==725])]
    for variant,puzzle,op,solutions in column_data:
        pairs=[[a,b] for x,y,a,b in solutions]
        details={
         'carry':('7 + 6 = 13: viết 3, nhớ 1 sang hàng chục.','Muốn hàng chục của tổng là 6 và nhớ 1 sang hàng trăm, A + B + 1 = 16, tức A + B = 15. Hàng trăm 3 + 2 + 1 = 6.'),
         'exchange':('2 không trừ được 7, đổi một chục: 12 − 7 = 5.','Hàng chục cần đổi tiếp một trăm: A + 10 − 1 − B = 2, tức B = A + 7. Hàng trăm còn 7 rồi 7 − 3 = 4.'),
         'coupled':('8 + 7 = 15: viết 5, nhớ 1 sang hàng chục.','Hàng chục 4 + B + 1 = 12 nên B = 7, nhớ 1. Hàng trăm A + 3 + 1 = 7 nên A = 3.')
        }[variant]
        add('column_multi_blank',variant,f'Điền các chữ số A, B vào {puzzle}. A và B là hai ô độc lập, có thể cùng chữ số; số hàng trăm không được là 0. Giữ mọi chữ số và dấu khác. Tìm tất cả cặp (A,B), giải thích nhớ hoặc đổi theo cột, không tự giả sử nghiệm duy nhất.','Mọi cặp chữ số và cách kiểm',hs('Các ô ở các hàng khác nhau phải cùng làm cho một phép tính đúng.','Đi từ hàng đơn vị để xác định có nhớ hoặc phải đổi một chục.','Thay từng cặp vào cả phép tính, và kiểm còn trường hợp nào khác.'),[st('Kiểm cột đơn vị','Cột đơn vị quyết định nhớ hoặc đổi sang cột chục.',details[0],explanation=details[0]),st('Ràng buộc các ô','Mỗi lựa chọn phải đồng thời thỏa cột chục và hàng trăm.',str(pairs),explanation=details[1]),st('Kiểm từng phép hoàn chỉnh','Tính lại bằng giá trị toàn bộ các số.', '; '.join(f'{x} {"+" if op=="add" else "−"} {y} = {x+y if op=="add" else x-y}' for x,y,a,b in solutions),explanation='Danh sách bao gồm tất cả cặp hợp lệ; nhiều cặp nếu có đều được giữ.')],[ans(str(pairs))],dict(kind='columns',puzzle=puzzle,op=op,pairs=pairs))

    for variant,start,target in [('cycle','2413','1234'),('two_cycles','2143','1234'),('five_cards','35124','12345')]:
        route=swap_route(start,target)
        current=list(start);states=[start]
        for i,j in route:current[i-1],current[j-1]=current[j-1],current[i-1];states.append(''.join(current))
        lower={
          'cycle':'Ban đầu cả bốn vị trí sai. Không cặp thẻ nào đổi cho nhau mà cả hai về đúng vị trí. Lần đầu sửa được nhiều nhất một vị trí; thêm một lần chỉ sửa được nhiều nhất hai vị trí nữa. Vì vậy hai lần chưa thể sửa đủ bốn vị trí.',
          'two_cycles':'Ban đầu cả bốn vị trí sai, một lần chỉ tác động hai vị trí nên một lần không thể sửa đủ bốn.',
          'five_cards':'Ban đầu cả năm vị trí sai; hai lần đổi tác động nhiều nhất bốn vị trí nên ít nhất một vị trí sai không được chạm. Vì vậy cần ít nhất ba lần.'
        }[variant]
        add('minimum_pair_swaps',variant,f'Dãy thẻ hiện tại là {", ".join(start)}. Đích là {", ".join(target)}. Mỗi lần được chọn bất kỳ hai vị trí và đổi chỗ hai thẻ đó; không xóa, thêm hay trượt thẻ. Đánh vị trí từ trái qua phải bắt đầu 1. Tìm số lần ít nhất và một chuỗi đổi đạt đích.','Số lần ít nhất và chuỗi đổi',hs('Một lần đổi chỉ tác động hai vị trí đã chọn.','Theo dõi các thẻ chưa đúng vị trí; viết lại dãy sau mỗi lần.','Cần vừa có cách đạt đích vừa có lý do không thể dùng ít lần hơn.'),[st('Theo chuỗi đổi hợp lệ','Đưa thẻ cần thiết về vị trí, giữ nguyên kho thẻ.',str(route),explanation='Dãy lần lượt: '+' → '.join(states)),st('Chứng minh ít nhất','Đếm các vị trí sai có thể được sửa trong ít lần đổi hơn.',len(route),explanation=lower+' Chuỗi đã cho đạt đúng số lần này.')],[ans(len(route),'lần'),ans(str(route),quantity='Cặp vị trí theo thứ tự')],dict(kind='swap',start=start,target=target,route=route,minimum=len(route)))

    for variant,digits,total in [('choose_cut','3527',62),('unequal_lengths','12636',162),('reject_reordering','4826',92)]:
        cuts=[i for i in range(1,len(digits)) if digits[i]!='0' and int(digits[:i])+int(digits[i:])==total]
        # Third task is an impossibility check, not an invented successful cut.
        equations=[digits[:i]+' + '+digits[i:]+' = '+str(int(digits[:i])+int(digits[i:])) for i in range(1,len(digits))]
        add('insert_single_plus',variant,f'Giữ nguyên thứ tự dãy chữ số {digits}. Chèn đúng một dấu + vào giữa hai chữ số để tổng bằng {total}. Không đổi chỗ, xóa hay thêm chữ số; hai số hạng không có 0 đứng đầu. Tìm mọi vị trí chèn, hoặc giải thích nếu không có.','Vị trí chèn hợp lệ hoặc chứng minh không có',hs('Chèn dấu chia dãy thành hai đoạn liên tiếp, không phải chia thành các thẻ tùy chọn.','Xét lần lượt mỗi khe giữa hai chữ số.','Tính tổng ở mọi khe hợp lệ rồi đối chiếu đích.'),[st('Xét đủ các khe','Mọi cách chèn đúng một dấu phải chọn một trong các khe liên tiếp.','; '.join(equations),explanation='Các chữ số vẫn đúng thứ tự gốc trong từng phép cộng.'),st('Đối chiếu đích','Chỉ giữ khe cho tổng đúng bằng đích.',str(cuts),explanation='Vị trí i nghĩa là chèn sau chữ số thứ i; danh sách rỗng nghĩa là không có cách theo đúng luật.')],[ans(str(cuts),quantity='Vị trí sau chữ số')],dict(kind='insert_plus',digits=digits,total=total,cuts=cuts))

    for variant,prefix,n,ndigits in [('prepend',4,583,3),('zero_inside',6,2050,4),('inverse_difference',7,326,3)]:
        new=prefix*10**ndigits+n;delta=new-n
        add('prefix_difference',variant,f'Số N có đúng {ndigits} chữ số. Viết thêm chữ số {prefix} vào ngay bên trái N, giữ nguyên tất cả chữ số của N. Hiệu số mới trừ N có phụ thuộc vào N không? Giải thích bằng hàng và kiểm thêm với N = {n}.','Hiệu không đổi và phép kiểm',hs('Viết thêm bên trái tạo một hàng mới; các chữ số cũ có dịch sang phải trên giá trị hàng không?','Tách số mới thành đóng góp của chữ số thêm và phần N.','Trừ lại phần N, rồi kiểm bằng ví dụ đã cho.'),[st('Tách theo hàng','Phần N giữ nguyên giá trị, chữ số mới nằm ở hàng ngay trên N.',f'{prefix} × {10**ndigits} + N',explanation='Không phải nhân N với mười, vì chữ số được viết phía bên trái.'),st('Lấy hiệu','Hai phần N bằng nhau nên triệt tiêu khi trừ.',delta,f'{prefix}*{10**ndigits}',explanation='Hiệu không phụ thuộc cách chọn các chữ số của N, chỉ cần N có đúng số chữ số đã nêu.'),st('Kiểm ví dụ','Thử với N cụ thể để đối chiếu việc ghép.',delta,f'{new}-{n}',explanation=f'Ghép được {new}; lấy số này bớt {n} khớp hiệu theo hàng.')],[ans(delta),ans('Không phụ thuộc N nếu giữ đúng số chữ số',quantity='Tính phụ thuộc')],dict(kind='prefix',prefix=prefix,n=n,digits=ndigits,new=new,difference=delta))

    for variant,n,out in [('unique',87642,88000),('multiple',83001,83000),('unchanged',85000,85000)]:
        places=[10**k for k in range(1,6)];valid=[p for p in places if ((n+p//2)//p)*p==out]
        names={10:'chục',100:'trăm',1000:'nghìn',10000:'chục nghìn',100000:'trăm nghìn'}
        add('infer_rounding_place',variant,f'Một bản ghi làm tròn số {n} được {out}. Quy tắc: xét chữ số ngay bên phải hàng làm tròn, từ 5 trở lên tăng hàng đó, dưới 5 giữ; các hàng thấp hơn thành 0. Chỉ xét hàng chục, trăm, nghìn, chục nghìn, trăm nghìn. Tìm tất cả hàng có thể đã dùng, không mặc định chỉ một hàng.','Mọi hàng làm tròn phù hợp',hs('Số chữ số 0 ở cuối kết quả chưa chắc xác định duy nhất hàng làm tròn.','Thử từng hàng được cho với cùng một quy tắc.','Giữ mọi hàng cho đúng số đầu ra, kể cả khi giá trị không thay đổi.'),[st('Kiểm từng hàng','Đầu vào và đầu ra đã biết nên có thể kiểm trực tiếp từng quy tắc.','; '.join(f'{names[p]}: {((n+p//2)//p)*p}' for p in places),explanation='Mỗi kết quả chỉ dùng hàng đang xét, không làm tròn liên tiếp qua nhiều hàng.'),st('Giữ đủ các khả năng','Đối chiếu với đúng số được ghi.',', '.join(names[p] for p in valid),explanation='Nếu nhiều hàng cho cùng đầu ra, bản ghi không đủ để chọn riêng một hàng.')],[ans(', '.join(names[p] for p in valid))],dict(kind='round_place',n=n,out=out,places=places,valid=valid))

    for variant,frac in [('find_pair',Fraction(5,6)),('another_whole',Fraction(7,12)),('all_pairs',Fraction(2,3))]:
        pairs=unit_pairs(frac)
        add('unit_fraction_decomposition',variant,f'Viết {frac} thành tổng đúng hai phân số có tử số 1, mẫu là số tự nhiên dương khác nhau. Không tính hai cách đổi thứ tự là khác. Tìm mọi cặp mẫu, giải thích kiểm bằng quy đồng.','Mọi cặp mẫu khác nhau',hs('Hai phân số đều dương; có thể gọi mẫu nhỏ hơn là a và mẫu lớn hơn là b.','So tổng với hai lần phân số có mẫu nhỏ hơn để giới hạn số mẫu phải thử.','Quy đồng để kiểm tổng và kiểm hai mẫu thật sự khác nhau.'),[st('Giới hạn mẫu nhỏ','Vì a < b nên tổng lớn hơn 1/a và nhỏ hơn 2/a.',f'{1/frac} < a < {2/frac}',explanation='Thử các số tự nhiên trong khoảng này là đủ, không phải thử vô hạn mẫu.'),st('Tìm cặp mẫu','Với mỗi a, phần còn lại quyết định duy nhất 1/b.',str(pairs),explanation='Chỉ giữ phần còn lại có dạng một chia số tự nhiên và b lớn hơn a.'),st('Kiểm tổng','Dùng quy đồng đối chiếu chính xác phân số ban đầu.',str(frac),f'1/{pairs[0][0]}+1/{pairs[0][1]}',explanation='Mọi cặp liệt kê đều có hai mẫu khác nhau; các a còn lại đã bị loại theo phần dư.')],[ans(str(pairs),quantity='(mẫu nhỏ, mẫu lớn)')],dict(kind='unit_pairs',fraction=str(frac),pairs=pairs))

    for variant,count,fractions in [('check_claims',10,['1/4','2/5']),('tiled_whole',18,['2/9','1/4']),('multiple_possible',12,['1/3','5/6'])]:
        vals=[Fraction(f)*count for f in fractions];possible=[v.denominator==1 for v in vals]
        add('discrete_fraction_integrality',variant,f'Có {count} miếng thẻ rời bằng nhau. Chỉ được lấy nguyên miếng, không cắt và không ghép thêm. Hai lời kể riêng về một lần lấy là A: lấy {fractions[0]} số miếng ban đầu; B: lấy {fractions[1]} số miếng ban đầu. Với mỗi lời kể, kiểm có thể xảy ra theo số lượng hay không. Không biết lần lấy thật đã chọn mấy miếng, nên không kết luận lời có thể xảy ra chắc chắn đã xảy ra.','Khả năng theo số lượng của A, B',hs('Một miếng rời được đếm bằng số tự nhiên.','Tính phần của tổng rồi kiểm có nguyên miếng hay cần cắt.','Khả năng theo số lượng khác với biết sự kiện thực tế đã xảy ra.'),[st('Đối chiếu lời A','Lấy phân số của tổng cho số miếng mà lời kể đòi hỏi.',str(vals[0]),f'{count}*({fractions[0]})','miếng',explanation='Nếu kết quả không nguyên thì mâu thuẫn điều kiện không cắt.'),st('Đối chiếu lời B','Dùng cùng số miếng ban đầu cho lời kể riêng này.',str(vals[1]),f'{count}*({fractions[1]})','miếng',explanation='Không cộng hai lời kể thành một lần lấy; đang kiểm từng lời độc lập.'),st('Kết luận trong phạm vi dữ kiện','Số nguyên từ không đến tổng là khả thi về số lượng.',f'A: {"có thể" if possible[0] else "không thể"}; B: {"có thể" if possible[1] else "không thể"}',explanation='Lời có thể xảy ra chưa được xác nhận là đúng với lần lấy thật khi chưa có bản ghi.')],[ans(str(possible),quantity='A, B khả thi về số lượng')],dict(kind='integrality',count=count,fractions=fractions,values=list(map(str,vals)),possible=possible))

    for variant,domain,kind in [('denominator',[0,1,2],'quotient'),('numerator',[1,2,4],'product'),('zero_boundary',[0,2,5],'difference')]:
        expressions=[f'18/(3-{m})' if kind=='quotient' else f'7*{m}+5' if kind=='product' else f'40-6*{m}' for m in domain]
        values=[evaluate(e,'fraction') for e in expressions];best=max(values);args=[m for m,v in zip(domain,values) if v==best]
        form={'quotient':'18 : (3 − m)','product':'7 × m + 5','difference':'40 − 6 × m'}[kind]
        add('finite_parameter_extrema',variant,f'Chỉ xét m trong tập {domain}. Tính biểu thức {form} ở từng giá trị được phép, rồi tìm giá trị lớn nhất và tất cả m đạt giá trị ấy. Với phép chia phải kiểm số chia khác 0.','Bảng giá trị và cực đại trên tập đã cho',hs('Giữ đúng tập giá trị được phép và thứ tự phép tính.','Thay lần lượt từng giá trị; nếu có số chia, kiểm trước khi tính.','So bảng đã đủ giá trị, không suy cực đại ngoài miền.'),[st(f'Thay m = {m}','Giá trị của biểu thức theo đúng giá trị m được phép.',str(v),e,explanation='Tính trong ngoặc trước nếu có; đơn vị là số thuần túy.') for m,e,v in zip(domain,expressions,values)]+[st('So sánh trên miền','Mọi giá trị được phép đã xét.',f'lớn nhất {best}; m = {args}',explanation='Kết luận chỉ cho tập m của đề, không cho mọi số tự nhiên.')],[ans(str(best),quantity='Giá trị lớn nhất'),ans(str(args),quantity='m đạt lớn nhất')],dict(kind='parameter',domain=domain,expressions=expressions,values=list(map(str,values)),args=args))

    cancel=[('matching_factors','(8*11*15)/(15*4*11)',Fraction(2),'Các thừa số 11, 15 và phần 4 trong 8 được rút gọn ở cả tử và mẫu.'),('sum_boundary','(6+24)/(6+4)',Fraction(3),'Tử và mẫu là tổng; phải tính từng tổng hoặc đặt nhân tử chung hợp lệ, không gạch riêng các số 6.'),('distributed_product','(7*5+7*3)/(7*6)',Fraction(4,3),'Đặt thừa số chung 7 ở toàn bộ tử rồi mới rút gọn với thừa số 7 ở mẫu.')]
    for variant,expression,value,why in cancel:
        add('structural_product_cancel',variant,f'Tính {expression}. Nêu rõ khi nào được rút gọn thừa số ở tử và mẫu; không được gạch tùy ý một số hạng trong tổng. Kiểm bằng cách tính riêng cả tử và mẫu.','Kết quả và rút gọn hợp lệ',hs('Phân biệt một thừa số của cả biểu thức với một số hạng trong tổng.','Chỉ rút gọn khi cùng chia cả tử và cả mẫu cho một số khác 0.','Tính riêng tử và mẫu để đối chiếu cách rút gọn.'),[st('Nhận cấu trúc','Rút gọn dựa vào nhân tử chung của toàn bộ tử và mẫu.',why,explanation=why),st('Tính và kiểm','Giá trị thương giữ nguyên khi chia cả tử và mẫu cùng thừa số khác không.',str(value),expression,explanation='Đối chiếu cách nhân hoặc cộng đầy đủ cho cùng giá trị; không thay đổi riêng một phía.')],[ans(str(value))],dict(kind='structural_arithmetic',expression=expression,value=str(value)))

    for variant,multiplier,wrong,x in [('unshifted_21',21,111,37),('unshifted_32',32,145,29),('explain_written_rule',41,190,38)]:
        a,b=divmod(multiplier,10);assert wrong==(a+b)*x
        add('reverse_algorithm_error',variant,f'Một bạn nhân số tự nhiên X với {multiplier}. Bản mô tả lỗi ghi rõ: tính hai tích riêng X × {b} và X × {a}, rồi cộng chúng cùng cột, không dịch tích ứng với hàng chục. Kết quả sai theo đúng cách này là {wrong}. Không có lỗi nào khác. Tìm X và kết quả đúng của X × {multiplier}. Chỉ dựa quy trình lỗi đã nêu.','X và tích đúng',hs('Dùng đúng quy tắc lỗi được mô tả, không tự thêm lỗi tính khác.','Viết kết quả sai thành tổng hai tích riêng chưa có hệ số hàng chục.','Thế X vào cả quy tắc lỗi và phép nhân đúng để kiểm hai yêu cầu.'),[st('Gộp phần đã tính sai','Hai tích riêng chưa dịch cùng có thừa số X.',f'({a}+{b}) × X = {wrong}',explanation='Đây là mô tả toán học của lỗi đã được cung cấp, không suy đoán ý nghĩ của bạn.'),st('Tìm số ban đầu','Chia kết quả sai cho tổng hai chữ số của số nhân.',x,f'{wrong}/({a}+{b})',explanation='Thay X lại vào hai tích riêng chưa dịch cho đúng số kết quả sai.'),st('Tính tích đúng','Chữ số hàng chục biểu thị chục nên tích riêng tương ứng phải nhân mười.',x*multiplier,f'{x}*{multiplier}',explanation='Kiểm bằng cách tách số nhân thành phần chục cộng đơn vị.')],[ans(x,quantity='X'),ans(x*multiplier,quantity='Tích đúng')],dict(kind='reverse_error',multiplier=multiplier,wrong=wrong,x=x,correct=x*multiplier))

    filters=[('thousands_and_parity',[527406,572406,527460,527405],'Chữ số hàng chục nghìn là 2, chữ số hàng chục là 0 và số là số chẵn.',lambda n:str(n)[1]=='2' and str(n)[-2]=='0' and n%2==0),('class_pattern',[7042305,7042035,7402305,7042304],'Lớp nghìn gồm 042 và chữ số hàng đơn vị là 5.',lambda n:n//1000%1000==42 and n%10==5),('two_positions',[305072,350072,305702,305073],'Chữ số hàng nghìn là 5, hàng trăm là 0 và số là số chẵn.',lambda n:n//1000%10==5 and n//100%10==0 and n%2==0)]
    for variant,numbers,rule,predicate in filters:
        valid=[n for n in numbers if predicate(n)]
        add('conjunctive_numeral_filter',variant,f'Các thẻ ghi {numbers}. Chỉ chọn thẻ đồng thời thỏa mọi điều kiện: {rule} Ghi mọi thẻ được chọn và nêu vì sao từng thẻ còn lại bị loại. Mỗi thẻ là một số đã viết đầy đủ, không sửa chữ số.','Tập thẻ thỏa giao các điều kiện',hs('Từ đồng thời yêu cầu mọi điều kiện đều đúng trên cùng một thẻ.','Lập hàng và lớp của từng số rồi kiểm thêm điều kiện cuối.','Thẻ đạt một phần chưa đủ; kiểm lại cả thẻ được chọn và bị loại.'),[st('Xét từng thẻ','Đọc chữ số theo đúng hàng hoặc lớp rồi kiểm từng điều kiện.', '; '.join(f'{n}: {"đạt đủ" if predicate(n) else "không đạt đủ"}' for n in numbers),explanation='Hàng nghìn khác lớp nghìn; số chẵn quyết định bởi hàng đơn vị.'),st('Lấy giao các điều kiện','Chỉ nhận thẻ có mọi điều kiện đúng.',str(valid),explanation='Không nối các nhóm đạt riêng lẻ thành hợp các nhóm; mọi thẻ còn lại không thỏa ít nhất một điều kiện.')],[ans(str(valid))],dict(kind='numeral_filter',variant=variant,numbers=numbers,result=valid,rule=rule))
    return ROWS

def swap_route(start,target):
    q=deque([(start,[])]);seen={start}
    while q:
        s,route=q.popleft()
        if s==target:return route
        for i,j in combinations(range(len(s)),2):
            t=list(s);t[i],t[j]=t[j],t[i];t=''.join(t)
            if t not in seen:seen.add(t);q.append((t,route+[[i+1,j+1]]))
    raise AssertionError('unreachable')

def unit_pairs(f):
    # With a < b, 1/a < f < 2/a; this is a mathematically finite range.
    result=[]
    for a in range(1,int(2/f)+1):
        rest=f-Fraction(1,a)
        if rest>0 and rest.numerator==1:
            b=rest.denominator
            if b>a:result.append([a,b])
    return result

def refine_content(rows):
    """Concrete reasoning repairs identified by actual author/peer reading."""
    for r in rows:
        family=r['topic'];o=r['oracle_evidence'];steps=r['worked_steps']
        if family=='abacus_budget' and o['want']=='nhỏ nhất':
            steps[-1]['explanation']='Đủ mười ba vòng. Đã để tối đa chín vòng ở đơn vị, phần còn lại ở chục. Cách phân bố khác phải chuyển ít nhất một vòng sang hàng cao hơn, làm giá trị tăng.'
        if family=='prefix_difference':
            text='Đối chiếu hàng của từng chữ số cũ trước và sau khi viết thêm ở bên trái.'
            r['initial_guidance']=[text];r['hints'][0]['hint']=text
        if family=='unit_fraction_decomposition':
            f=Fraction(o['fraction'])
            descriptions={
              '5/6':('Mẫu nhỏ không thể là 1 vì một phần đã bằng 1. Nếu mẫu nhỏ từ 3 trở lên thì tổng nhỏ hơn 2/3, mà 2/3 < 5/6. Vậy chỉ cần thử mẫu nhỏ 2.', 'Với mẫu nhỏ 2: 5/6 − 1/2 = 1/3, nên mẫu còn lại là 3.'),
              '7/12':('Mẫu nhỏ không thể là 1. Nếu mẫu nhỏ từ 4 trở lên thì tổng nhỏ hơn 2/4 = 1/2, mà 1/2 < 7/12. Chỉ cần thử mẫu nhỏ 2 hoặc 3.', 'Nếu mẫu nhỏ 2: 7/12 − 1/2 = 1/12. Nếu mẫu nhỏ 3: 7/12 − 1/3 = 1/4. Hai trường hợp đều cho mẫu còn lại lớn hơn mẫu đang thử.'),
              '2/3':('Mẫu nhỏ không thể là 1. Nếu mẫu nhỏ từ 3 trở lên thì cả hai phân số không lớn hơn 1/3, và phân số có mẫu lớn hơn còn nhỏ hơn 1/3; tổng phải nhỏ hơn 2/3. Vậy chỉ cần thử mẫu nhỏ 2.', 'Với mẫu nhỏ 2: 2/3 − 1/2 = 1/6, nên mẫu còn lại là 6.')
            }[str(f)]
            steps[0].update(reason='Mẫu lớn hơn cho phân số đơn vị nhỏ hơn, nên có thể chặn số trường hợp cần thử.',result=descriptions[0],explanation=descriptions[0])
            steps[1]['reason']='Với mỗi mẫu nhỏ đang thử, lấy phân số đã cho trừ phân số đơn vị tương ứng để tìm phần còn lại.'
            steps[1]['explanation']=descriptions[1]
            steps[2]['explanation']='; '.join(f'1/{a} + 1/{b} = {Fraction(1,a)+Fraction(1,b)}' for a,b in o['pairs'])+'. Đã kiểm tất cả mẫu nhỏ còn lại và hai mẫu luôn khác nhau.'
            r['initial_guidance']=['Hai mẫu khác nhau; hãy phân biệt phân số có mẫu nhỏ hơn với phân số có mẫu lớn hơn.']
            r['hints'][0]['hint']=r['initial_guidance'][0]
        if family=='discrete_fraction_integrality':
            labels=[f'{chr(65+i)}: '+('có thể về số lượng, chưa biết đã xảy ra' if v else 'không thể theo luật nguyên miếng') for i,v in enumerate(o['possible'])]
            r['expected_answer'][0]['result']='; '.join(labels)
        if family=='structural_product_cancel':
            tree=ast.parse(o['expression'],mode='eval').body
            top=ast.get_source_segment(o['expression'],tree.left)
            bottom=ast.get_source_segment(o['expression'],tree.right)
            numeric_top=evaluate(top,'fraction');numeric_bottom=evaluate(bottom,'fraction')
            steps.insert(1,st('Kiểm tử','Tính đầy đủ tử trước khi đối chiếu rút gọn.',str(numeric_top),top,explanation='Mọi số hạng hoặc thừa số thuộc tử đều được giữ.'))
            steps.insert(2,st('Kiểm mẫu','Tính đầy đủ mẫu và kiểm khác không.',str(numeric_bottom),bottom,explanation='Không gạch riêng số hạng của tổng; mẫu tính được khác không.'))
            steps[-1]['explanation']=f'Tính riêng được tử {numeric_top}, mẫu {numeric_bottom}; thương {o["value"]}, khớp phép rút gọn hợp lệ.'
        if family=='reverse_algorithm_error':
            a,b=divmod(o['multiplier'],10);x=o['x']
            steps.insert(2,st('Thế vào bản mô tả lỗi','Phải thu lại đúng kết quả sai được cung cấp.',o['wrong'],f'{x}*{b}+{x}*{a}',explanation=f'{x} × {b} + {x} × {a} = {o["wrong"]}; đúng với quy tắc cùng cột đã ghi, không thêm giả định lỗi khác.'))
            steps[-1]['explanation']=f'Phần chục là {a*10}: {x} × {a*10} + {x} × {b} = {o["correct"]}. Đây là phép tách số nhân đúng.'
        if family=='conjunctive_numeral_filter':
            details=[]
            for n in o['numbers']:
                variant=o['variant']
                if variant=='thousands_and_parity':
                    tests=[(n//10000%10==2,f'chục nghìn là {n//10000%10}, cần 2'),(n//10%10==0,f'chục là {n//10%10}, cần 0'),(n%2==0,f'đơn vị {n%10}, cần chẵn')]
                elif variant=='class_pattern':
                    tests=[(n//1000%1000==42,f'lớp nghìn là {n//1000%1000:03d}, cần 042'),(n%10==5,f'đơn vị là {n%10}, cần 5')]
                else:
                    tests=[(n//1000%10==5,f'nghìn là {n//1000%10}, cần 5'),(n//100%10==0,f'trăm là {n//100%10}, cần 0'),(n%2==0,f'đơn vị {n%10}, cần chẵn')]
                failed=[message for ok,message in tests if not ok]
                details.append(str(n)+(': loại vì '+', '.join(failed) if failed else ': đúng tất cả điều kiện'))
            steps[0]['explanation']='; '.join(details)+'.'
        for i,s in enumerate(steps):s['step_id']=f's{i}'
        r['canonical_case']['operations']=[s['expression'] for s in steps if s.get('expression')]
    return rows

def main():
    OUT.mkdir(exist_ok=True)
    rows=refine_content(author());assert len(rows)==48
    old={json.loads(l)['sample_id'] for l in (RUN/'current_sources.jsonl').read_bytes().splitlines()}
    assert not old.intersection(r['sample_id'] for r in rows)
    for r in rows:
        assert len(r['hints'])==3
        for s in r['worked_steps']:
            if s['expression']:
                assert evaluate(s['expression'],'fraction')==Fraction(s['result']), (r['sample_id'],s)
    (OUT/'draft_cases.jsonl').write_bytes(b''.join((L.canonical_json(r)+'\n').encode() for r in rows))
    (OUT/'family_comparison_pending.json').write_text(json.dumps(FAMILIES,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(drafts=len(rows),families=len(FAMILIES),status='DRAFT_AWAITING_CONTENT_CROSS_REVIEW',sha256=hashlib.sha256((OUT/'draft_cases.jsonl').read_bytes()).hexdigest())))

if __name__=='__main__':main()
