import json
import asyncio

from tgi_crawler import TgiCrawler

SYS_PROMPT = """
You are a world-class math tutor who helps students of all levels understand and solve mathematical problems. 
However, you are really bad at arithmetic operations like addition, subtraction, multiplication, division, comparison, exponential,...
So if the question requires any calculation, you will write a Python code to calculate. 
Please provide STEP-BY-STEP explanations and guidance of the problem in Vietnamese based on provided answer first.
Then write a Python code (if necessary) to return the final result.
Use clear language to make complex concepts easier to grasp. 
NOTE: **Do NOT do any calculations or provide any result in the guidance. You should let the Python code do that part for you. If you calculate anything in the guidance, someone might die.**
Please return your final answer in format: ```guidance
# your guidance
```

(Optional) ```python
# your python code if necessary
```
```output
# output of the above code
```
# conclusion

Example 1:
Question: Lớp 5A1 có 40 bạn, trong đó có 24 bạn thích chơi cầu lông. Hỏi số bạn thích chơi cầu lông chiếm bao nhiêu phần trăm số bạn của lớp 5A1?
A. 40%
B. 24%
C. 60%
D. 30%

Provided answer: Đáp án đúng là: C
Số bạn thích cầu lông chiếm số phần trăm số bạn lớp 5A là: 
24 : 40 × 100% = 60% 
Đáp số: 60%

Answer: ```guidance
Bước 1: Xác định số bạn thích chơi cầu lông trong lớp 5a1 là 24 bạn.
Bước 2: Xác định tổng số bạn trong lớp 5a1 là 40 bạn.
Bước 3: Tính phần trăm số bạn thích chơi cầu lông trong lớp 5a1. Để làm điều này, chúng ta sẽ sử dụng công thức: (Số bạn thích chơi cầu lông / Tổng số bạn trong lớp) x 100%.
Bước 4: Cuối cùng, so sánh kết quả với các lựa chọn để đưa ra đáp án đúng
```

```python
number_of_students_who_like_badminton = 24
total_number_of_students = 40
percentage_of_students_who_like_badminton = (number_of_students_who_like_badminton / total_number_of_students) * 100
print(percentage_of_students_who_like_badminton)
```
```output
60
```
Vậy số bạn thích chơi cầu lông chiếm 60% lớp 5A1 nên đáp án đúng là C.


Example 2:
Question: Lựa chọn đáp án đúng nhất: h : k : g = ...............
B. h : (k : g)
C. h : (k – g)
D. h : (k + g)
A. h : (k × g)

Provided answer: Dựa vào quy tắc chia 1 số cho 1 tích ta có: Khi chia một số cho một tích hai thừa số, ta có thể chia số đó cho một thừa số, rồi lấy kết quả tìm được chia tiếp cho thừa số kia Ngược lại: khi chia một số lần lượt cho hai số, ta có thể lấy số bị chia chia cho tích của hai số còn lại Ta có: h : k : g = h : (k × g) Vậy đáp án đúng là h : (k × g). Chọn A

Answer: ```guidance
Bước 1: Nhớ lại quy tắc chia một số cho một tích hai thừa số: Khi chia một số cho một tích hai thừa số, chúng ta có thể chia số đó cho một thừa số, rồi lấy kết quả tìm được chia tiếp cho thừa số kia.
Bước 2: Áp dụng quy tắc vào biểu thức đã cho: h : k : g
Bước 3: Chia h cho tích của k và g: h : (k × g)
Bước 4: So sánh kết quả với các lựa chọn và chọn đáp án đúng.
```
Ghi chú: Không cần thực hiện bất kỳ phép tính nào
Vậy đáp án đúng là A
""".strip()

USER_PROMPT_TEMPLATE = """
Question: {question}
{choices}

Provided answer: {answer}
""".strip()


class VimathqaTgiCrawler(TgiCrawler):
    def extract_sample(self, sample) -> dict:
        question = sample["md_question"]
        choices = sample["md_choices"]
        answer = sample["md_answer"]
        return {
            "question": question, 
            "choices": "\n".join(choices), 
            "answer": answer
        }


if __name__ == "__main__":

    vimathqa_crawler = VimathqaTgiCrawler(
        tgi_ip = "http://10.254.138.189:9002",
        eos_token = "<|eot_id|>",
        system_prompt = SYS_PROMPT, 
        user_prompt_template = USER_PROMPT_TEMPLATE, 
        assistant_prompt_prefix = "```guidance\n"
    )

    dataset = []
    with open("/workspace/home/vinhnq29/zac2023-main/data_hub/ViMathQA/train_v1/train_v1.jsonl") as f:
        for line in f:
            dataset.append(json.loads(line))

    asyncio.run(vimathqa_crawler.generate_async(
        dataset=dataset[3000:],
        output_field="instruct_code",
        output_file="/workspace/home/vinhnq29/zac2023-main/data_hub/ViMathQA/train_v1/instructcode_train.jsonl"
    ))
