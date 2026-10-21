"""Render deterministic demonstration lessons through the production storyboard/encoder.
No model calls; answers are submitted to the actual lesson checker.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai/runtime'))
from app.tutoring import lesson, video
from app.tutoring.video_render import render_movie,draw_scene

out=Path(__file__).parent
examples=[('garden','Tìm tổng số cây trong vườn',[
    lesson.Step(title='Tìm phần cây táo và xoài',explanation='Cây táo và cây xoài là hai nhóm cây khác nhau. Ta cộng hai phân số chỉ hai nhóm này.',question='Tổng hai phân số là bao nhiêu?',expression='1/3+2/5',fractionNotation=True),
    lesson.Step(title='Tìm phần cây cam',explanation='Cả vườn là một đơn vị. Bớt phần cây táo và xoài thì được phần cây cam.',question='Phần cây cam là bao nhiêu?',expression='1-{s0}',fractionNotation=True),
    lesson.Step(title='Tìm số cây của cả vườn',explanation='Đã biết số cây cam và phần mà nhóm cây cam chiếm. Ta chia số cây cam cho phân số đó.',question='Trong vườn có tất cả bao nhiêu cây?',expression='16/{s1}',unit='cây')],['11/15','4/15','60']),
    ('pencils','Tìm số bút Lan còn lại',[
    lesson.Step(title='Tìm số bút sau khi được cho thêm',explanation='Khi được cho thêm bút, số bút của Lan tăng lên. Ta cộng số bút ban đầu với số bút mẹ cho.',question='Lúc này Lan có bao nhiêu bút?',expression='24+13',unit='bút'),
    lesson.Step(title='Tìm số bút còn lại',explanation='Lan cho bạn bớt một số bút. Ta lấy số bút vừa tìm được trừ số bút đã cho.',question='Lan còn lại bao nhiêu bút?',expression='{s0}-5',unit='bút')],['37','32'])]
rows=[]
def render_snapshot(key,goal,request):
    scenes=video.storyboard(request);start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='mathvision-demo-render-') as temp:
        path,duration=render_movie(scenes,Path(temp),lambda value:None)
        shutil.copy2(path,out/f'{key}-voiced.mp4')
    seconds=round(time.perf_counter()-start,2)
    draw_scene(scenes[1],1,len(scenes),out/f'{key}-poster.png')
    rows.append({'example':key,'goal':goal,'scenes':len(scenes),'renderSeconds':seconds,'videoSeconds':round(duration,2),'bytes':(out/f'{key}-voiced.mp4').stat().st_size,'storyboard':[scene.__dict__ for scene in scenes]})
    print(f'{key}: {seconds}s rendering, {duration:.1f}s voiced movie',flush=True)
for key,goal,steps,answers in examples:
    session_id=f'personal-video-demo-{key}-12345'
    lesson._sessions[session_id]=lesson.Session('sample-pupil',lesson.Plan(topic='Phân số' if key=='garden' else 'Toán có lời văn',goal=goal,steps=steps,finalAnswerStep=len(steps)-1),time.monotonic()+3600,givens=frozenset({'1','2','3','5','16','24','13'}))
    if key=='garden':render_snapshot('garden-step',goal,video.VideoRequest(owner='sample-pupil',sessionId=session_id,revision=0))
    for index,answer in enumerate(answers):
        result=lesson.answer_lesson(lesson.TurnRequest(owner='sample-pupil',sessionId=session_id,revision=index,answer=answer))
        assert result.status in {'CORRECT','COMPLETE'}
    render_snapshot(key,goal,video.VideoRequest(owner='sample-pupil',sessionId=session_id,revision=len(answers)))
(out/'samples.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
