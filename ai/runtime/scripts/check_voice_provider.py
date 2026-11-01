"""Readiness check only. Never prints credentials or provisions paid resources."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings
if __name__=='__main__':
    print(json.dumps(dict(provider=settings.speech_provider,azureKeyConfigured=bool(settings.azure_speech_key.get_secret_value()),
        azureRegionConfigured=bool(settings.azure_speech_region),voices=['Giọng nam','Giọng nữ'],
        officialRouteReady=bool(settings.azure_speech_key.get_secret_value() and settings.azure_speech_region),
        quotaDocumentation='https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits')))
