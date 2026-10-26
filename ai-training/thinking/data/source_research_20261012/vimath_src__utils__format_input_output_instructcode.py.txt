import os
from transformers import AutoTokenizer
import argparse
import random
from datasets import load_dataset
import json
from string import punctuation
import re

# random.seed(42)
OUTPUT_PATTERN = re.compile(r"```output([\s\S]*?)```")

def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help=""
    )
    parser.add_argument(
        "--eos_token",
        type=str,
        default=None,
        help=""
    )
    parser.add_argument(
        "--chat_template",
        type=str,
        default=None,
        help=""
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help=""
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help=""
    )
    args = parser.parse_args()

    # Sanity checks
    if not args.model_name or not args.output_file or not args.input_file:
        raise ValueError()
    
    return args


def normalize_name(name: str):
    return name.translate(
        str.maketrans(punctuation, "_"*len(punctuation))
    ).lower()


SYS_PREFIX = [
    "Với vai trò là giáo viên dạy kèm môn toán, nhiệm vụ của bạn là giúp học sinh ở mọi cấp độ nắm bắt và giải quyết các vấn đề toán học. Tuy nhiên, bạn có thể thấy khó khăn với các phép toán số học cơ bản. Để đối phó với vấn đề này, bạn sẽ cung cấp hướng dẫn từng bước và viết mã Python theo hướng dẫn đó để thực hiện tất cả các phép tính cần thiết và cung cấp kết quả cuối cùng mỗi khi một câu hỏi đòi hỏi phép tính toán.",
    "Là một giáo viên dạy kèm môn toán, mục tiêu chính của bạn là giúp đỡ học sinh ở mọi cấp độ hiểu và giải quyết các vấn đề toán học. Tuy nhiên, bạn gặp khó khăn với các phép toán cơ bản như cộng, trừ, nhân, chia, so sánh, lũy thừa, v.v. Để khắc phục điều này, nếu một câu hỏi yêu cầu bất kỳ phép tính số học nào, bạn sẽ cung cấp hướng dẫn từng bước và viết mã Python theo hướng dẫn đó để thực hiện tất cả các phép tính cần thiết và trả lại kết quả cuối cùng.",
    "Trong vai trò là gia sư môn toán, nhiệm vụ của bạn là hỗ trợ học sinh ở mọi trình độ hiểu và giải quyết các bài toán. Tuy nhiên, bạn có thể gặp rắc rối với những phép tính cơ bản như cộng, trừ, nhân, chia,... Để khắc phục điều này, bạn sẽ đưa ra hướng dẫn chi tiết từng bước và viết mã Python theo hướng dẫn đó để thực hiện tất cả các phép tính cần thiết và cung cấp kết quả cuối cùng mỗi khi một câu hỏi yêu cầu tính toán.",
    "Là một giáo viên dạy kèm môn toán, mục tiêu chính của bạn là giúp đỡ học sinh ở các cấp độ kỹ năng khác nhau nắm bắt và giải quyết các vấn đề toán học. Tuy nhiên, bạn có thể gặp khó khăn với việc tính toán cơ bản. Để bù đắp cho điều này, khi một câu hỏi liên quan đến các phép tính toán số học, bạn sẽ cung cấp một giải thích chi tiết, từng bước một và tạo ra một đoạn mã Python phản ánh những bước này, thực hiện các phép tính cần thiết và trả về câu trả lời cuối cùng.",
    "Bạn là một gia sư toán học đẳng cấp thế giới. Bạn rất giỏi trong việc giúp đỡ học sinh ở mọi cấp độ hiểu và giải quyết các vấn đề toán học phức tạp. Tuy nhiên, bạn lại khá yếu trong việc thực hiện các phép toán cơ bản như cộng, trừ, nhân, chia, so sánh, lũy thừa,.v.v. Do đó, khi một câu hỏi yêu cầu bất kỳ hình thức tính toán nào, bạn sẽ cung cấp một hướng dẫn chi tiết, từng bước một và viết một đoạn mã Python theo hướng dẫn này để thực hiện tất cả các phép tính cần thiết và cung cấp câu trả lời cuối cùng."
]
SYS_SUFFIX = r"""
Lưu ý: 
- Bạn không cần phải viết mã Python nếu bài toán chỉ hỏi về lý thuyết hoặc không yêu cầu tính toán.
- Nếu phải sử dụng giá trị pi, hãy gán pi = 3.14
- Hãy đặt đáp án mà bạn lựa chọn vào \box{}
Hãy đưa ra câu trả lời theo định dạng: ```guidance
# your guidance
```

(Optional) ```python
# your python code if necessary
```
```output
# output of the above code
```
# your conclusion
""".strip()


vi_instruction_multiple_choices_prompts = [
    "Giải bài toán trắc nghiệm sau:",
    "Hãy từng bước giải quyết câu hỏi trắc nghiệm sau:",
    "Suy luận từng bước để trả lời câu hỏi trắc nghiệm dưới đây:",
    "Trả lời câu hỏi sau:",
    "Giải bài toán dưới đây:",
    "Hãy từng bước giải quyết bài toán dưới đây:",
    "Sử dụng kiến thức của bạn để giải bài toán sau:",
    "Suy luận từng bước để trả lời câu hỏi dưới đây:",
    "Suy luận từng bước để giải bài toán sau đây:",
    "Giải bài toán dưới đây bằng cách suy luận từng bước:"
]

USER_PROMPT_TEMPLATE = """
{instruction}
{question}
{choices}
"""
    
    
    

if __name__ == "__main__":
    args = parse_args()
    models_hub = "/workspace/home/vinhnq29/zac2023-main/models_hub"
    tokenizer = AutoTokenizer.from_pretrained(
        os.path.join(models_hub, args.model_name)
    )
    if args.eos_token:
        tokenizer.eos_token = args.eos_token
    if args.chat_template and not tokenizer.chat_template:
        tokenizer.chat_template = args.chat_template
        
    train_data = []
    with open(args.input_file) as f:
        for line in f:
            train_data.append(json.loads(line))
        
    input_output_data  = []
    n_drop = 0
    for sample in train_data:
        system_prompt = random.choice(SYS_PREFIX)+"\n"+SYS_SUFFIX
        
        instruction = random.choice(vi_instruction_multiple_choices_prompts)
        question = sample["md_question"]
        choices = sample["md_choices"]
        choices = [x for x in choices if x]
        choices.sort(key=lambda choice: choice[0])
        choices="\n".join(choices)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            instruction=instruction,
            question=question,
            choices=choices
        ).strip()
        
        answer = sample["instruct_code"].strip()
        if len(answer) > 4000:
            continue
        if not (question and choices and answer):
            continue
        answer_parts = OUTPUT_PATTERN.split(answer)
        if len(answer_parts) == 3:
            input_output_data.append({"segments": [
                {
                    "label": False,
                    "text": tokenizer.apply_chat_template([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ], tokenize=False, add_generation_prompt=True)
                },
                {
                    "label": True,
                    "text": answer_parts[0]+"```output"
                },
                {
                    "label": False,
                    "text": answer_parts[1]+"```"
                },
                {
                    "label": True,
                    "text": answer_parts[2] + tokenizer.eos_token
                }
            ]})
        elif len(answer_parts) == 1:
            input_output_data.append({"segments": [
                {
                    "label": False,
                    "text": tokenizer.apply_chat_template([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ], tokenize=False, add_generation_prompt=True)
                },
                {
                    "label": True,
                    "text": answer + tokenizer.eos_token
                }
            ]})
        else:
            continue
        

    with open(args.output_file, "w") as f:
        f.write(json.dumps(
            input_output_data,
            indent=4,
            ensure_ascii=False
        ))

    # input_output_dataset = load_dataset(
    #     "json", 
    #     data_files=args.output_file,
    #     split="train"
    # )

    # input_output_dataset.push_to_hub(
    #     "vinhnq29/ViMathQA",
    #     "train_v1", split=f"input_output_{normalize_name(args.model_name)}",
    #     token="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"
    # )
