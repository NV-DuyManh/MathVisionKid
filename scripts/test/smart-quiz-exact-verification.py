"""Compile the real Quiz generator and independently solve its wording with Fraction.

No Spring, database, AI provider or third-party Python dependency is required.
Usage: python scripts/test/smart-quiz-exact-verification.py [--output result.json]
Requires Java 21+ on PATH.
"""
import argparse
import base64
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess
import tempfile

SOURCES = [
    ('trees', 'cây', 'Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?', Fraction(60)),
    ('books', 'quyển sách', 'Thư viện có 1/4 số sách là sách truyện, 3/8 số sách là sách khoa học, còn lại là sách tham khảo. Biết có 18 quyển sách tham khảo. Hỏi thư viện có tất cả bao nhiêu quyển sách?', Fraction(48)),
    ('candy', 'viên kẹo', 'Bé Mạnh có một số viên kẹo. Trong đó, 1/4 số kẹo là kẹo dâu, 2/5 số kẹo là kẹo cam, còn lại là kẹo chanh. Biết có 14 viên kẹo chanh. Hỏi bé Mạnh có tất cả bao nhiêu viên kẹo?', Fraction(40)),
    ('marbles', 'viên bi', 'Hộp bi có 3/8 số viên bi là bi đỏ, 1/4 số viên bi là bi xanh, còn lại là bi vàng. Biết số bi vàng là 18 viên bi. Hỏi hộp bi có tất cả bao nhiêu viên bi?', Fraction(48)),
]
PROBE = r'''
package com.mathvisionkids.api.quiz;
import java.util.*;
import java.nio.charset.StandardCharsets;
public class QuizExactProbe {
    static String encode(String text) {
        return Base64.getEncoder().encodeToString(text.getBytes(StandardCharsets.UTF_8));
    }
    public static void main(String[] args) {
        for (int i=0;i<args.length;i++) {
            var text=new String(Base64.getDecoder().decode(args[i]),StandardCharsets.UTF_8);
            var source=QuizMath.classify(text,true).orElseThrow();
            for (int seed=-1;seed<250;seed++) {
                Random random=seed<0 ? new Random(){ @Override public int nextInt(int bound) { return bound-1; } } : new Random(seed);
                var q=QuizMath.generate(source,random);
                System.out.println(i+"\t"+seed+"\t"+encode(q.question())+"\t"+q.answer()+"\t"+encode(q.unit())+"\t"+encode(q.solution()));
            }
        }
    }
}
'''


def verify(root):
    package = root / 'backend/business-api/src/main/java/com/mathvisionkids/api/quiz'
    with tempfile.TemporaryDirectory(prefix='quiz-exact-') as folder:
        target = Path(folder)
        probe = target / 'QuizExactProbe.java'
        probe.write_text(PROBE, encoding='utf-8')
        subprocess.run(['javac', '-encoding', 'UTF-8', '-d', folder,
                        str(package / 'Rational.java'), str(package / 'QuizMath.java'), str(probe)], check=True, capture_output=True)
        result = subprocess.run(['java', '-Dfile.encoding=UTF-8', '-cp', folder,
            'com.mathvisionkids.api.quiz.QuizExactProbe',
            *(base64.b64encode(source[2].encode()).decode() for source in SOURCES)],
            check=True, capture_output=True, encoding='utf-8')
    decode = lambda value: base64.b64decode(value).decode()
    examples = []
    total_checked = 0
    for line in result.stdout.splitlines():
        index, seed, encoded_question, answer, encoded_unit, encoded_solution = line.split('\t')
        name, source_unit, source_text, source_answer = SOURCES[int(index)]
        question, unit, solution = map(decode, (encoded_question, encoded_unit, encoded_solution))
        fractions = list(map(Fraction, re.findall(r'\b\d+/\d+\b', question)))
        assert len(fractions) == 2, question
        a, b = fractions
        counts = re.findall(r'\b(\d+) (?:quyển sách|viên kẹo|viên bi)\b', question)
        assert len(counts) == 1, question
        rest = 1 - a - b
        assert a > 0 and b > 0 and rest > 0, question
        count = Fraction(counts[0])
        whole = count / rest
        groups = [whole * a, whole * b, count]
        assert all(group > 0 and group.denominator == 1 for group in groups), question
        assert whole.denominator == 1 and whole == sum(groups) and whole == Fraction(answer), question
        source_fractions = list(map(Fraction, re.findall(r'\b\d+/\d+\b', source_text)))
        source_count = source_answer * (1 - sum(source_fractions))
        assert a not in source_fractions and b not in source_fractions, question
        assert count != source_count and whole != source_answer and unit != source_unit, question
        total_checked += 1
        if int(seed) in (-1, 0, 1):
            examples.append(dict(source=name, seed=int(seed), question=question, answer=str(whole),
                                 unit=unit, groups=list(map(str, groups)), solution=solution))
    assert total_checked == 1004
    return dict(status='PASS', verifier='Python fractions.Fraction, parsed from generated question text',
                checked=total_checked, randomVariants=1000, forcedFallbacks=4,
                sourceAnswers={source[0]: str(source[3]) for source in SOURCES}, examples=examples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(Path(__file__).resolve().parents[2])
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'examples'}, ensure_ascii=False))
