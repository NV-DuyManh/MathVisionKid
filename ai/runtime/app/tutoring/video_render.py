"""Offline, captioned H.264/AAC movies. No model or network calls."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import wave
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

MAX_BYTES = 16 * 1024 * 1024
MAX_SECONDS = 240


@dataclass(frozen=True)
class Scene:
    title: str
    text: str
    expression: str = ''
    answer: str = ''
    spoken: str = ''


def spoken_math(text: str) -> str:
    text = re.sub(r'(^|[=(]\s*)[-−]\s*(?=\d)',r'\1âm ',text)
    units={'km':'ki lô mét','dm':'đề xi mét','cm':'xăng ti mét','mm':'mi li mét','m':'mét'}
    text = re.sub(r'(?<![a-z])(km|dm|cm|mm|m)([²³])',lambda m:units[m[1]]+(' vuông' if m[2]=='²' else ' khối'),text)
    text = re.sub(r'(\d+)\s*/\s*(\d+)', r'\1 phần \2', text)
    text = re.sub(r'(?<=[\d)])\s*:\s*(?=[(\d])',' chia ',text)
    for symbol, word in [('+',' cộng '), ('−',' trừ '), ('-',' trừ '), ('×',' nhân '),
                         ('*',' nhân '), ('÷',' chia '), ('/',' chia '), ('=',' bằng '), ('%',' phần trăm ')]:
        text = text.replace(symbol, word)
    return re.sub(r'\s+', ' ', text.replace('(', ' mở ngoặc ').replace(')', ' đóng ngoặc ')).strip()


def run(args, deadline, **kwargs):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('Video rendering deadline')
    return subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=min(25, remaining), **kwargs)


def synthesize(text: str, path: Path, deadline: float, max_seconds=65):
    if os.name == 'nt':
        # Text and paths are JSON stdin, never interpolated into executable code.
        script = r'''$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';
        Add-Type -AssemblyName System.Runtime.WindowsRuntime;
        $p=ConvertFrom-Json([Console]::In.ReadToEnd());
        $s=New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer;
        $voices=[Windows.Media.SpeechSynthesis.SpeechSynthesizer,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime]::AllVoices;
        try { $v=$voices | Where-Object {$_.Language -eq 'vi-VN'} | Select-Object -First 1;
        if (!$v) {throw 'Vietnamese voice unavailable'};
        $s.Voice=$v; $s.Options.SpeakingRate=0.9;
        $method=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'} | Select-Object -First 1;
        $resultType=[Windows.Media.SpeechSynthesis.SpeechSynthesisStream,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime];
        $task=$method.MakeGenericMethod($resultType).Invoke($null,@($s.SynthesizeTextToStreamAsync($p.text))); $task.Wait();
        $stream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($task.Result);
        $file=[IO.File]::Create($p.path);try{$stream.CopyTo($file)}finally{$file.Dispose();$stream.Dispose()}
        } finally {if($s -is [IDisposable]){([IDisposable]$s).Dispose()}}'''
        run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script], deadline,
            input=json.dumps({'text': spoken_math(text), 'path': str(path)}).encode('ascii'),
            creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        engine = shutil.which('espeak-ng')
        if not engine:
            raise RuntimeError('Vietnamese speech engine unavailable')
        run([engine, '-v','vi','-s','150','-w',str(path),'--stdin'], deadline,
            input=spoken_math(text).encode('utf-8'))
    with wave.open(str(path), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate()
        if audio.getnframes() == 0 or not .1 < duration < max_seconds:
            raise ValueError('Invalid narration duration')
    return duration


def font(size, bold=False):
    parents = Path(__file__).resolve().parents
    candidates = ([parents[4]/'apps/student-mobile/assets/fonts'/('Nunito-ExtraBold.ttf' if bold else 'Nunito-Regular.ttf')] if len(parents)>4 else [])
    candidates.append(Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'))
    for file in candidates:
        if file.is_file():
            return ImageFont.truetype(str(file), size)
    raise RuntimeError('Vietnamese caption font unavailable')


def draw_scene(scene: Scene, index: int, total: int, path: Path):
    image = Image.new('RGB',(960,540),'#F3EEFC'); draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((26,22,934,518),radius=28,fill='white')
    draw.text((58,46),'MathVisionKid',font=font(19,True),fill='#7543CE')
    draw.text((750,48),f'CẢNH {index+1} / {total}',font=font(15,True),fill='#78668F')

    def lines(text, size, max_width):
        rows=[]; row=''; face=font(size)
        for word in text.split():
            candidate=(row+' '+word).strip()
            if row and draw.textlength(candidate,font=face)>max_width:
                rows.append(row); row=word
            else: row=candidate
        if row:rows.append(row)
        return rows

    title_rows=lines(scene.title,29,830)
    title_size=29 if len(title_rows)<=2 else 25
    y=95
    for row in lines(scene.title,title_size,830):
        draw.text((58,y),row,font=font(title_size,True),fill='#261B53'); y+=37
    body_rows=lines(scene.text,23,820)
    size=23 if len(body_rows)<=5 else 20
    for row in lines(scene.text,size,820):
        draw.text((60,y+15),row,font=font(size),fill='#685877'); y+=31
    y+=34
    equation=scene.expression+(f' = {scene.answer}' if scene.answer else '')
    if equation:
        math_size=32
        while math_size>16 and draw.textlength(equation,font=font(math_size,True))>804: math_size-=1
        draw.rounded_rectangle((58,y,902,y+64),radius=18,fill='#F1EAFD')
        draw.text((78,y+9),equation,font=font(math_size,True),fill='#6938CA'); y+=84
    # Only depict proper fractions that are literally present in this published step.
    fractions=re.findall(r'(?<!\d)(\d{1,2})\s*/\s*(\d{1,2})(?!\d)',equation)[:3]
    fractions=[(int(n),int(d)) for n,d in fractions if 0<=int(n)<=int(d) and 1<=int(d)<=24]
    if fractions and y+55<459:
        w=min(250,760//len(fractions)); gap=26
        for item,(n,d) in enumerate(fractions):
            x=60+item*(w+gap)
            for part in range(d):
                draw.rectangle((x+part*w/d,y,x+(part+1)*w/d-1,y+34),fill='#8C63DC' if part<n else '#EDE6F8',outline='white',width=2)
            draw.text((x,y+38),f'{n}/{d}',font=font(17,True),fill='#7042C9')
    draw.rounded_rectangle((54,477,906,502),radius=10,fill='#F6F1FC')
    draw.text((69,479),'Có lời giảng • Em có thể tạm dừng để xem kỹ.',font=font(15),fill='#78668F')
    if y>465:
        raise ValueError('Scene exceeds caption area')
    image.save(path)


def render_movie(scenes: list[Scene], directory: Path, progress):
    ffmpeg=shutil.which('ffmpeg'); ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        raise RuntimeError('Video encoder unavailable')
    deadline=time.monotonic()+100
    durations=[]; segments=[]
    for index,scene in enumerate(scenes):
        audio=directory/f'voice-{index}.wav'; frame=directory/f'scene-{index}.png'; output=directory/f'part-{index}.mp4'
        duration=synthesize(scene.spoken,audio,deadline)+.45
        durations.append(duration)
        if sum(durations)>MAX_SECONDS:
            raise ValueError('Video too long; use individual learning steps')
        draw_scene(scene,index,len(scenes),frame)
        run([ffmpeg,'-hide_banner','-loglevel','error','-y','-loop','1','-framerate','12','-i',str(frame),'-i',str(audio),
             '-t',str(duration),'-vf','fade=t=in:st=0:d=0.18' if index else 'null','-af','apad=pad_dur=0.45','-c:v','libx264',
             '-preset','ultrafast','-crf','25','-pix_fmt','yuv420p','-c:a','aac','-b:a','80k','-ar','24000','-ac','1','-threads','1',str(output)],deadline)
        segments.append(output.name);progress(round((index+1)/len(scenes)*90))
    playlist=directory/'parts.txt';playlist.write_text(''.join(f"file '{name}'\n" for name in segments),encoding='utf-8')
    output=directory/'lesson.mp4'
    run([ffmpeg,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','1','-i',str(playlist),'-c','copy','-movflags','+faststart',str(output)],deadline)
    probe=json.loads(run([ffprobe,'-v','error','-show_entries','stream=codec_type:format=duration','-of','json',str(output)],deadline).stdout)
    duration=float(probe['format']['duration'])
    if not any(stream['codec_type']=='audio' for stream in probe['streams']) or not 0<duration<=MAX_SECONDS+2 or output.stat().st_size>MAX_BYTES:
        raise ValueError('Invalid voiced video')
    for index in range(len(scenes)):
        for name in (f'voice-{index}.wav',f'scene-{index}.png',f'part-{index}.mp4'):
            (directory/name).unlink(missing_ok=True)
    playlist.unlink(missing_ok=True)
    return output,duration
