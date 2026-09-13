import urllib.request
import json
import sys

def post_multipart(url, fields, files):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = bytearray()
    for k, v in fields.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode('utf-8'))
    for k, (filename, data, content_type) in files.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode('utf-8'))
        body.extend(data)
        body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    req = urllib.request.Request(url, data=bytes(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

if __name__ == '__main__':
    import os
    base_url = os.environ.get('BASE_URL', 'http://localhost:8080/api/v1')
    with open('scratch/python_exam_test.jpg', 'rb') as f:
        img_data = f.read()

    res = post_multipart(f'{base_url}/ocr/multiline/detect', {'privacyConfirmed': 'true'}, {'image': ('test.jpg', img_data, 'image/jpeg')})
    print(f"Unauthenticated /detect: status=200, lines={len(res.get('lines', []))}")
