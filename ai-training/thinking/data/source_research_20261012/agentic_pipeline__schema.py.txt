"""Schema dữ liệu (dùng dataclasses để chạy được bằng stdlib, không cần cài gì)."""
from dataclasses import dataclass, asdict


@dataclass
class Seed:
    question: str
    answer: str


@dataclass
class Sample:
    id: str
    question: str
    chain_of_thought: str
    final_answer: str
    verify: dict
    difficulty: dict
    topic: str = ""
    source_seed: str = ""
    lang: str = "vi"

    def to_dict(self) -> dict:
        return asdict(self)
