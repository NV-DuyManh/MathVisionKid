import array
import io
import json
import math
from pathlib import Path
import subprocess
from PIL import Image, ImageStat

out=Path(__file__).parent
rows=[]
for movie in out.glob('*-voiced.mp4'):
    probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,sample_rate:format=duration','-of','json',str(movie)],capture_output=True,check=True).stdout)
    assert any(s['codec_type']=='audio' and s['codec_name']=='aac' for s in probe['streams'])
    pcm=subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-map','0:a:0','-f','s16le','-ac','1','-ar','8000','pipe:1'],capture_output=True,check=True).stdout
    samples=array.array('h',pcm);rms=math.sqrt(sum(n*n for n in samples)/len(samples))/32768
    assert rms>.001,'Silent audio'
    frame=subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1'],capture_output=True,check=True).stdout
    brightness=sum(ImageStat.Stat(Image.open(io.BytesIO(frame)).convert('RGB')).mean)/3
    assert brightness>80,f'{movie.name}: blank black opening frame'
    rows.append({'file':movie.name,'duration':float(probe['format']['duration']),'bytes':movie.stat().st_size,'streams':probe['streams'],'audioRms':round(rms,5),'firstFrameBrightness':round(brightness,1)})
(out/'video-metadata.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
