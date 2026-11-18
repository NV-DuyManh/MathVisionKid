"""Build public curriculum Vietnamese fallback speech with the existing offline engine.

Only the bundled lesson inventory is read. No account, model, or provider is used.
Reruns verify/reuse existing paragraphs and atomically publish a complete manifest.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import zlib
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tutoring import curriculum, lesson, media_preparation
from app.tutoring.curriculum_audio import AUDIO_DIRECTORY, paragraph_key
from app.tutoring.speech_render import run, synthesize

PART_DIRECTORY = Path(__file__).resolve().parents[3] / '.local-artifacts' / 'curriculum-audio-parts'


def scripts():
    entries = json.loads(curriculum.SOURCE.read_text(encoding='utf-8'))['entries']
    paragraphs = set()
    for entry in entries:
        request = lesson.LessonRequest(owner='public-curriculum-build', problemText=entry['problemText'], problemConfirmed=True)
        base = lesson.Plan.model_validate(entry['plan'])
        lesson.validate_plan(base, request, lesson.formula_constants(request.problemText))
        plans = [base]
        try:
            reading = lesson.source_understanding(request.problemText)
        except lesson.UnderstandingUnsupported:
            try:
                reading = lesson.labelled_understanding(request.problemText)
            except lesson.UnderstandingUnsupported:
                reading = []
        if reading:
            if reading[-1].choices == ['Đúng', 'Sai']:
                quoted = re.search('«(.*?)»', reading[-1].question).group(1)
                # Runtime comprehension randomly quotes either the fact or question.
                for quote, truth in [(reading[0].correctChoice, 'Đúng'), (reading[1].correctChoice, 'Sai')]:
                    check = reading[-1].model_copy(update={
                        'question': reading[-1].question.replace(quoted, quote),
                        'hints': [hint.replace(quoted, quote) for hint in reading[-1].hints],
                        'correctChoice': truth,
                    })
                    plans.append(lesson.prepend_understanding(base, [*reading[:-1], check]))
            else:
                plans.append(lesson.prepend_understanding(base, reading))
        for plan in plans:
            session = lesson.Session(request.owner, plan, time.monotonic() + 3600,
                givens=frozenset(lesson.numeric_values(request.problemText)) | lesson.formula_constants(request.problemText),
                problem_text=request.problemText)
            initial, reviews = media_preparation.project_scripts(session)
            paragraphs.update(' '.join(part.split()) for parts in [*initial, *reviews.values()] for part in parts)
            for step in plan.steps:
                hints = step.hints or lesson.calculation_hints(step, session.answers)
                for index, hint in enumerate(hints):
                    spoken = lesson.teaching_at(hint, session.answers)
                    if index == 0 and (not lesson.numeric_values(spoken).issubset(set(session.givens) | lesson.numeric_values(' '.join(session.answers)))
                            or re.search(r'\d\s*=\s*\d', spoken)):
                        spoken = lesson.calculation_hints(step, session.answers)[0]
                    if index > 0 and step.fractionNotation and step.expression:
                        details = lesson.fraction_working(lesson.expression_at(step, session.answers))
                        if details:
                            spoken = (details[0] + '\n' + spoken)[:500]
                    paragraphs.add(' '.join(spoken.split()))
                session.hint_count = 2
                public = lesson.present('private-projection', session).step
                paragraphs.update(' '.join(part.split()) for part in [*public.guidance, public.question])
                value = step.correctChoice if step.choices else str(lesson.calculate_exact(lesson.expression_at(step, session.answers)))
                session.completed.append(lesson.completed_step(step, session, value))
                session.answers.append(value)
                session.hint_count = 0
        paragraphs.add(' '.join(entry['problemText'].split()))
    return sorted(paragraphs)


def render(text):
    key = paragraph_key(text)
    path = PART_DIRECTORY / (key + '.pcm.zlib')
    if path.is_file():
        try:
            pcm = zlib.decompress(path.read_bytes())
            if pcm and len(pcm) % 2 == 0 and any(pcm):
                return key, sha256(pcm).hexdigest()
        except (OSError, zlib.error):
            pass
    with tempfile.TemporaryDirectory(prefix='mathvision-curriculum-') as directory:
        source = Path(directory) / 'source.wav'
        output = Path(directory) / 'output.pcm'
        deadline = time.monotonic() + 55
        synthesize(text, source, deadline, max_seconds=100)
        run([shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
             '-ar', '16000', '-ac', '1', '-f', 's16le', '-threads', '1', str(output)], deadline)
        pcm = output.read_bytes()
        if not pcm or len(pcm) % 2 or not any(pcm):
            raise ValueError('Silent or incomplete curriculum audio')
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(zlib.compress(pcm, 9))
        temporary.replace(path)
        return key, sha256(pcm).hexdigest()


def main():
    AUDIO_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PART_DIRECTORY.mkdir(parents=True, exist_ok=True)
    paragraphs = scripts()
    rendered = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(render, text) for text in paragraphs]
        for index, future in enumerate(as_completed(futures), 1):
            key, digest = future.result()
            rendered[key] = digest
            if index % 25 == 0:
                print(f'{index}/{len(paragraphs)} public paragraphs ready', flush=True)
    # Keep public bundles below repository hosting file-size limits.
    for prefix in '0123456789abcdef':
        archive_path = AUDIO_DIRECTORY / f'public_speech_{prefix}.tmp'
        with ZipFile(archive_path, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
            for key in sorted(rendered):
                if key.startswith(prefix):
                    pcm = zlib.decompress((PART_DIRECTORY / (key + '.pcm.zlib')).read_bytes())
                    archive.writestr(key + '.pcm', pcm)
        archive_path.replace(AUDIO_DIRECTORY / f'public_speech_{prefix}.zip')
    document = {'version': 1, 'voice': 'Microsoft An (vi-VN)', 'sampleRate': 16000,
                'paragraphs': dict(sorted(rendered.items()))}
    temporary = AUDIO_DIRECTORY / 'manifest.tmp'
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(AUDIO_DIRECTORY / 'manifest.json')
    print(f'Prepared {len(rendered)} public Vietnamese paragraphs', flush=True)


if __name__ == '__main__':
    main()
