"""Minimal synthetic JSON probes. Never logs credentials, response bodies or student data."""
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import httpx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings, _ENV_FILES

def probe(name):
    enabled=getattr(settings,name+'_enabled')
    keys=[key.strip() for key in getattr(settings,name+'_api_keys').split(',') if key.strip()]
    model=settings.groq_primary_vision_model if name=='groq' else settings.gemini_model
    result={'enabled':enabled,'keyCount':len(keys),'model':model}
    if not enabled or not keys:
        result['probe']='NOT_CONFIGURED'; return name,result
    if name=='groq':
        url='https://api.groq.com/openai/v1/chat/completions'
        payload={'model':model,'messages':[{'role':'user','content':'Return JSON only: {"ok":true}'}], 'temperature':0,'max_tokens':32,'response_format':{'type':'json_object'}}
        headers={'Authorization':'Bearer '+keys[0]}
    else:
        url='https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent'
        payload={'contents':[{'parts':[{'text':'Return JSON only: {"ok":true}'}]}],'generationConfig':{'temperature':0,'responseMimeType':'application/json'}}
        headers={'x-goog-api-key':keys[0]}
    try:
        with httpx.Client(timeout=25) as client:
            response=client.post(url,json=payload,headers=headers)
            result['httpStatus']=response.status_code
            if response.status_code>=400:
                result['category']='AUTH_INVALID' if response.status_code==401 else 'FORBIDDEN' if response.status_code==403 else 'RATE_LIMIT_OR_QUOTA' if response.status_code==429 else 'MODEL_OR_REQUEST' if response.status_code in (400,404) else 'PROVIDER_UNAVAILABLE'
                result['responseFormat']='json' if 'application/json' in response.headers.get('content-type','') else 'other'
                return name,result
            data=response.json()
            raw=data['choices'][0]['message']['content'] if name=='groq' else data['candidates'][0]['content']['parts'][0]['text']
            result['jsonValid']=json.loads(raw).get('ok') is True
    except HTTPError as error:
        result['httpStatus']=error.code
        result['category']='AUTH' if error.code in (401,403) else 'RATE_LIMIT_OR_QUOTA' if error.code==429 else 'MODEL_OR_REQUEST' if error.code in (400,404) else 'PROVIDER_UNAVAILABLE'
    except Exception as error:
        result['category']=type(error).__name__
    return name,result

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with ThreadPoolExecutor(2) as workers:
        result=dict(workers.map(probe,['groq','gemini']))
    result['envFiles']=[{'path':str(Path(path).relative_to(Path(__file__).resolve().parents[3])) if Path(path).is_relative_to(Path(__file__).resolve().parents[3]) else Path(path).name,'exists':Path(path).is_file()} for path in _ENV_FILES]
    dest=Path(__file__).resolve().parents[3]/'report/smart-quiz-runtime-root-cause/providers.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
