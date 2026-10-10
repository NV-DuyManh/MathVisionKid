"""Test-only candidate responses. Production always asks the configured model."""
import json
from unittest.mock import AsyncMock
from app.tutoring import lesson


def step(**values):
    title = values.get("title", "Tìm đại lượng cần biết")
    defaults = dict(title=title,
        explanation="Cần tìm đại lượng này trước để có đủ dữ kiện trả lời câu hỏi. Đối chiếu ý nghĩa của các lượng đã cho rồi chọn phép tính.",
        question="Đại lượng ở bước này bằng bao nhiêu?",
        hints=["Đọc lại ý nghĩa của các lượng đã cho trước khi chọn phép tính.",
               "Viết phép tính phù hợp với các lượng ấy rồi tính theo thứ tự."],
        guidance=["Đọc lại câu hỏi và xác định đại lượng cần tìm ở bước này. Đối chiếu dữ kiện gắn với đại lượng đó.",
                  "Cần tìm lượng này trước khi dùng nó trong bước sau. Viết phép tính theo ý nghĩa của các lượng đã cho.",
                  "Thực hiện các phép tính theo đúng thứ tự và tự ghi kết quả. Viết câu lời giải, phép tính và đơn vị phù hợp."],
        solutionSentence=(title + " là:") if values.get("expression") else "")
    return {**defaults, **values}


def review_for(candidate, results=None):
    # Used ONLY for session/transport tests. Review rejection tests supply an
    # independently specified result or failed check instead.
    plan = lesson.Plan.model_validate(candidate)
    answers=[]
    for item in plan.steps:
        answers.append(str(lesson.calculate_exact(lesson.expression_at(item, answers))) if item.expression else item.correctChoice)
    if results is None:
        index=plan.finalAnswerStep
        results=[] if index is None else [dict(stepIndex=index, answer=answers[index], unit=plan.steps[index].unit)]
    return dict(sourceFaithful=True, mathematicsCorrect=True, answersQuestion=True, teachingClear=True, results=results)


def mock_generation(monkeypatch, candidate, results=None):
    cloud=AsyncMock(side_effect=[candidate, review_for(candidate, results)])
    monkeypatch.setattr(lesson, "_generate", cloud)
    return cloud


def geometry(source, work=""):
    import re
    a=re.search(r"AB = (\d+)", source)[1]
    b=re.search(r"CD = (\d+)", source)[1]
    area=re.search(r"ACD là (\d+)", source)[1]
    excerpt=""
    rows=work.splitlines()
    for index, row in enumerate(rows):
        if "chiều cao" in row:
            excerpt=row + "\n" + rows[index+1]
    return dict(topic="Diện tích hình thang", goal="Tìm chiều cao rồi diện tích hình thang.", finalAnswerStep=2, steps=[
        step(title="Tìm điều còn thiếu", question="Cần tìm đại lượng nào trước?", choices=["Chiều cao", "Chu vi", "Đường chéo AC"], correctChoice="Chiều cao"),
        step(title="Tìm chiều cao chung", expression=f"{area}*2/{b}", unit="cm", workExcerpt=excerpt),
        step(title="Tính diện tích hình thang", expression=f"({a}+{b})*{{s1}}/2", unit="cm²"),
    ])


def garden_candidate(a="1", b="3", c="2", d="5", count="16"):
    return dict(topic="Phần cây trong vườn", goal="Tìm phần còn lại rồi số cây cả vườn.", finalAnswerStep=2, steps=[
        step(title="Tính phần cây táo và xoài", expression=f"{a}/{b}+{c}/{d}", unit="phần", fractionNotation=True),
        step(title="Tính phần cây cam", expression="1-{s0}", unit="phần", fractionNotation=True,
             guidance=["Phần cây táo và xoài là {s0} của cả vườn. Cây cam là phần còn lại nên cần bớt phần đã biết khỏi cả vườn.",
                       "Viết cả vườn thành phân số cùng mẫu với phần cây đã biết. Trừ các tử số rồi giữ mẫu chung để tìm phần còn lại.",
                       "Viết câu lời giải nêu phần cây cam trong vườn. Sau đó ghi phép trừ và kết quả em tự tính, giữ dạng phân số chính xác."]),
        step(title="Tìm số cây cả vườn", expression=f"{count}/{{s1}}", unit="cây", fractionNotation=True,
             guidance=["Phần cây cam chiếm {s1} cả vườn. Số cây cam đã biết tương ứng với phần này, chưa phải cả vườn.",
                       f"Lấy {count} chia cho {{s1_numerator}} để tìm lượng trong một phần nhỏ. Sau đó nhân với {{s1_denominator}} để gộp đủ các phần của cả vườn.",
                       "Viết câu lời giải nêu số cây có tất cả trong vườn. Sau đó ghi phép tính, kết quả em tự tính và đơn vị cây."]),
    ])
