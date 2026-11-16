"""Publish curriculum metadata and worked examples without private grading plans."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'ai/runtime/app/tutoring/data/primary_math_curriculum.json'
TARGET = ROOT / 'apps/student-mobile/src/data/primaryMathCurriculumData.json'
PUBLIC_FIELDS = ('id', 'grade', 'section', 'order', 'week', 'source', 'bookSeries', 'topic', 'title',
                 'problemText', 'guidance', 'difficulty', 'sampleSolution')


def export():
    entries = json.loads(SOURCE.read_text(encoding='utf-8'))['entries']
    public = [{name: row[name] for name in PUBLIC_FIELDS} for row in entries]
    TARGET.write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return len(public)


if __name__ == '__main__':
    print(f'Exported {export()} curriculum exercises')
