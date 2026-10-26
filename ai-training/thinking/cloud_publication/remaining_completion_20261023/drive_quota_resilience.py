"""Bounded backoff for explicit Drive rate limits; no dataset/config changes."""
import functools,json,threading,time
_active_status={}

def is_rate_limit(error):
    status=getattr(getattr(error,'resp',None),'status',None)
    if status==429:return True
    if status!=403:return False
    try:
        body=json.loads(error.content)
        reasons={x.get('reason') for x in body.get('error',{}).get('errors',[])}
        return bool(reasons & {'rateLimitExceeded','userRateLimitExceeded'})
    except (ValueError,TypeError,AttributeError):return False

def install(status):
    global _active_status
    _active_status=status
    from googleapiclient import http
    if getattr(http.HttpRequest.execute,'mathvision_drive_quota',False):return
    lock=threading.Lock();last=[0.0]
    def wrap(original):
        @functools.wraps(original)
        def bounded(*args,**kwargs):
            for attempt in range(7):
                with lock:
                    delay=1.25-(time.monotonic()-last[0])
                    if delay>0:time.sleep(delay)
                    last[0]=time.monotonic()
                try:return original(*args,**kwargs)
                except Exception as error:
                    if not is_rate_limit(error) or attempt==6:raise
                    _active_status['drive_rate_limit_backoff']={'attempt':attempt+1,'wait_seconds':60,'action':'RETRY_SAME_REQUEST_NO_ROW_ADVANCE'}
                    time.sleep(60)
        bounded.mathvision_drive_quota=True
        return bounded
    http.HttpRequest.execute=wrap(http.HttpRequest.execute)
    http.HttpRequest.next_chunk=wrap(http.HttpRequest.next_chunk)
    http.MediaIoBaseDownload.next_chunk=wrap(http.MediaIoBaseDownload.next_chunk)
    status['drive_quota_resilience']={'request_spacing_seconds':1.25,'explicit_rate_limit_wait_seconds':60,'max_outer_retries':6,'other_errors_unchanged':True}
