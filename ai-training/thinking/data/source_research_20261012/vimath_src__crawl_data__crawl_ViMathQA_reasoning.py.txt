import json
import asyncio
import argparse

from tgi_crawler import TgiCrawler
from vllm_crawler import VllmCrawler


def parse_args():
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument(
        "--input_path",
        type=astr,
        default=None,
        help="The absolute path to link file."
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=None,
        help="The absolute path to output file"
    )
    args = parser.parse_args()

    # Sanity checks
    if args.input_path is None or args.output_path is None:
        raise ValueError("Need both a input file and a output file")
    
    return args


HEADER = r"""You are a math tutor who helps students of all levels understand and solve mathematical problems. Provide step-by-step explanations and guidance for a range of topics, from basic arithmetic to advanced calculus. Use clear language and visual aids to make complex concepts easier to grasp and put your final answer in \box{}.
"""

SYS_PROMPT = HEADER + r"""
---------------------------------
Example 1: 
Question: Trong các số thập phân 30,516; 30,561; 30,651; 30,615. Số thập phân lớn nhất là: 
A. 30,516 
B. 30,561 
C. 30,651 
D. 30,615

Your Answer: Để tìm số thập phân lớn nhất trong các số 30,516; 30,561; 30,651; 30,615, chúng ta cần so sánh các số thập phân này với nhau. Đầu tiên, chúng ta có thể thấy rằng tất cả các số đều có phần nguyên là 30, nên chúng ta chỉ cần so sánh phần thập phân. Phần thập phân của các số lần lượt là 516, 561, 651, 615. Trong các phần thập phân này, 651 là lớn nhất. Do đó, số thập phân lớn nhất là 30,651. Vậy đáp án là \box{C}

---------------------------------
Example 2:
Question: Kết quả của phép tính 7 × 10 – 14 là 
A. 46 
B. 56 
C. 66 
D. 54

Your answer: Để tìm kết quả của phép tính 7 × 10 – 14, chúng ta cần thực hiện phép tính theo thứ tự. Đầu tiên, chúng ta nhân 7 với 10, được 70. Sau đó, chúng ta trừ 14 từ 70, được 70 - 14 = 56. Vậy kết quả của phép tính trên là 56. Đáp án đúng là \box{B}.

---------------------------------
Example 3:
Question: Một hình tam giác có diện tích 384 cm2, chiều cao 24 cm. Vậy cạnh đáy của hình tam giác đó là: 
A. 16 cm 
B. 32 cm 
C. 16 cm2 
D. 32 cm2

Your answer: Để tìm cạnh đáy của hình tam giác, chúng ta cần sử dụng công thức diện tích hình tam giác: diện tích = (chiều cao × cạnh đáy) / 2. Trong trường hợp này, diện tích hình tam giác là 384 cm2 và chiều cao là 24 cm. Để tìm cạnh đáy, chúng ta cần biến đổi công thức trên thành cạnh đáy = 2 × diện tích / chiều cao. Thay các giá trị đã biết vào công thức, chúng ta có cạnh đáy = 2 × 384 : 24 = 32 cm. Do đó, cạnh đáy của hình tam giác đó là 32 cm. Vậy đáp án là \box{B}.

---------------------------------
Example 4:
Question: 18 phút 36 giây  +  12 phút 12 giây  ?   nửa giờ 
A. > 
B. < 
C. =

Your answer: Để so sánh 18 phút 36 giây + 12 phút 12 giây với nửa giờ, chúng ta cần tính tổng của 18 phút 36 giây và 12 phút 12 giây. Khi cộng hai thời gian này lại, chúng ta được 30 phút 48 giây. Nửa giờ bằng 30 phút. Vì 30 phút 48 giây lớn hơn 30 phút, nên chúng ta có thể kết luận rằng 18 phút 36 giây + 12 phút 12 giây lớn hơn nửa giờ. Do đó, đáp án đúng là \box{A: >}

---------------------------------
Example 5:
Question: Giải bài toán dưới đây: Cho x là số liền sau của số 2016 và y là số liền trước của số 2018. Hãy so sánh x và y. 
A. x = y 
B. x < y 
C. x > y

Your answer: Để so sánh x và y, chúng ta cần tìm ra giá trị của x và y. Đầu tiên, số liền sau của số 2016 là 2017, do đó x = 2017. Tiếp theo, số liền trước của số 2018 là 2017, do đó y = 2017. Vì x và y đều bằng 2017, nên chúng ta có thể kết luận rằng x = y. Vậy đáp án là \box{A: x = y}.
"""

USER_PROMPT_TEMPLATE = """
Question: {question}
{choices}
""".strip()


# class VimathqaTgiCrawler(TgiCrawler):
#     def extract_sample(self, sample) -> dict:
#         question = sample["md_question"]
#         choices = sample["md_choices"]
#         answer = sample["md_answer"]
#         return {
#             "question": question, 
#             "choices": "\n".join(choices), 
#             "answer": answer
#         }
        

class VimathqaVllmCrawler(VllmCrawler):
    def extract_sample(self, sample) -> dict:
        question = sample["question"]
        choices = sample["choices"]
        return {
            "question": question, 
            "choices": "\n".join(choices), 
        }


if __name__ == "__main__":

    args = parse_args()

    # crawler = VimathqaTgiCrawler(
    #     tgi_ip = "http://10.254.138.189:9002",
    #     eos_token = "<|eot_id|>",
    #     system_prompt = SYS_PROMPT, 
    #     user_prompt_template = USER_PROMPT_TEMPLATE, 
    #     assistant_prompt_prefix = "```guidance\n"
    # )

    crawler = VimathqaVllmCrawler(
        endpoint_ip = "http://10.254.138.192:9002",
        model_name = "Meta-Llama-3-70B-Instruct",
        eos_token = "<|eot_id|>",
        system_prompt = SYS_PROMPT, 
        user_prompt_template = USER_PROMPT_TEMPLATE, 
        assistant_prompt_prefix = "Phân tích và suy luận: "
    )

    dataset = []
    with open(args.input_path) as f:
        for line in f:
            dataset.append(json.loads(line))

    asyncio.run(crawler.generate_async(
        dataset=dataset,
        output_field="instruct_code",
        output_file=args.output_path
    ))
