import json,types
from drive_quota_resilience import is_rate_limit

def error(code,reason):
    return types.SimpleNamespace(resp=types.SimpleNamespace(status=code),content=json.dumps({'error':{'errors':[{'reason':reason}]}}).encode())

def test_only_explicit_retryable_quota_errors():
    assert is_rate_limit(error(403,'rateLimitExceeded'))
    assert is_rate_limit(error(403,'userRateLimitExceeded'))
    assert is_rate_limit(error(429,'anything'))
    assert not is_rate_limit(error(403,'insufficientFilePermissions'))
    assert not is_rate_limit(error(403,'storageQuotaExceeded'))
    assert not is_rate_limit(error(500,'internalError'))
    assert not is_rate_limit(RuntimeError('network failure'))
