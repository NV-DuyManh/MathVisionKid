"""Install the existing speech renderer's portable FFmpeg prerequisite; no system PATH edits."""
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[2]
URL='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
cache=Path.home()/'.cache/mathvision-speech'
cache.mkdir(parents=True,exist_ok=True)
archive=cache/'ffmpeg-release-essentials.zip'
with urlopen(URL+'.sha256',timeout=30) as response:
    expected=re.search(r'[a-fA-F0-9]{64}',response.read().decode())[0].lower()
if not archive.exists() or hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()!=expected:
    with urlopen(URL,timeout=45) as source,archive.open('wb') as output:
        shutil.copyfileobj(source,output,1024*1024)
with archive.open('rb') as source:
    actual=hashlib.file_digest(source,'sha256').hexdigest()
if actual!=expected: raise RuntimeError('FFmpeg archive checksum mismatch')
dest=ROOT/'infra/local-runtime/tools/ffmpeg/bin'
dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as package:
    name=next(name for name in package.namelist() if name.endswith('/bin/ffmpeg.exe'))
    with package.open(name) as source,(dest/'ffmpeg.exe').open('wb') as output:
        shutil.copyfileobj(source,output)
    for name in package.namelist():
        if name.endswith('/LICENSE') or name.endswith('/LICENSE.txt'):
            (dest.parent/'LICENSE.txt').write_bytes(package.read(name)); break
result={'source':URL,'archiveSha256':actual,'checksumVerified':True,'systemPathChanged':False,'destination':'infra/local-runtime/tools/ffmpeg/bin/ffmpeg.exe'}
(ROOT/'report/smart-quiz-runtime-root-cause/ffmpeg-install.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Portable FFmpeg verified and installed for the existing speech renderer.')
