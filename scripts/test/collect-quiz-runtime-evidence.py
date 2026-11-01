"""Collect counts and artifact identities without exporting credentials or student records."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'report/smart-quiz-runtime-root-cause'
roots=[ET.parse(p).getroot() for p in (ROOT/'backend/business-api/build/test-results/test').glob('TEST-*.xml')]
result={'checkedAt':datetime.now(timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,encoding='utf-8').strip(),
        'backend':{'suites':len(roots),'tests':sum(int(r.get('tests',0)) for r in roots),'failures':sum(int(r.get('failures',0)) for r in roots),'errors':sum(int(r.get('errors',0)) for r in roots)}}
student=Path.home()/'quiz-runtime-final-student.json'
if student.exists():
    r=json.loads(student.read_text(encoding='utf-8'))
    result['student']={key:r[key] for key in ['numTotalTestSuites','numPassedTestSuites','numTotalTests','numPassedTests','numFailedTests']}
for name in ['live-api-results','real-lesson','voice-http','cloud-off','providers-disabled-http','providers-disabled-runtime','runtime-after','exact-math','providers']:
    file=OUT/(name+'.json')
    if file.exists(): result[name]=json.loads(file.read_text(encoding='utf-8'))
browser=OUT/'browser/browser-results.json'
if browser.exists():
    r=json.loads(browser.read_text(encoding='utf-8'))
    result['browser']={'checks':len(r.get('checks',[])),'failure':r.get('failure'),'exceptions':r.get('exceptions'),'speechPlaybackAvailable':r.get('speechPlaybackAvailable'),'physicalDevice':False}
review=OUT/'browser-work-review/browser-results.json'
if review.exists():
    r=json.loads(review.read_text(encoding='utf-8'))
    result['browserWorkReview']={'checks':len(r.get('checks',[])),'failure':r.get('failure'),'exceptions':r.get('exceptions'),'reviewMode':r.get('reviewMode'),'speechPlaybackAvailable':r.get('speechPlaybackAvailable')}
primary=OUT/'browser/browser-cloud-review-unavailable.json'
if primary.exists():
    r=json.loads(primary.read_text(encoding='utf-8'))
    result['primaryUiAcceptance']={'runtime':r.get('runtime'),'realTutorComplete':any(turn.get('status')=='COMPLETE' for turn in r.get('tutorTurns',[])),
        'bothQuizChoicesShown':any(check.get('label')=='Completion automatically shows both Quiz choices' and check.get('status')=='PASS' for check in r.get('checks',[])),
        'laterWorkReviewFailure':r.get('failure')}
earlier=OUT/'verification-earlier-complete-run.json'
if earlier.exists(): result['earlierFullBrowser']=json.loads(earlier.read_text(encoding='utf-8')).get('browser')
backup=Path.home()/'smart-quiz-runtime-baseline-20261028/manifest.json'
if backup.exists():
    before=json.loads(backup.read_text(encoding='utf-8'))
    result['wipAudit']={'baselineFiles':len(before),'missing':[name for name in before if not (ROOT/name).is_file()],
                       'changed':[name for name,digest in before.items() if (ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]}
result['physicalDeviceTested']=False
result['ownerFeedback']='Owner will test iPhone later; no native PASS is claimed.'
(OUT/'verification-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:result[key] for key in ['backend','student','browser','wipAudit'] if key in result},ensure_ascii=False,indent=2))
