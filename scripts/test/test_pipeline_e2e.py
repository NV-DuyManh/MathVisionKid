import urllib.request
import json
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def login(email="minh.student@mathvision.local", password="MathVision123!"):
    req = urllib.request.Request(
        'http://localhost:8080/api/v1/auth/login',
        data=json.dumps({'email': email, 'password': password}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        token = data.get('accessToken')
        print(f"[AUTH] Logged in as {email}, token obtained (len={len(token)})")
        return token

def post_multipart(url, fields, files, token=None):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = bytearray()
    
    for k, v in fields.items():
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode('utf-8'))
        body.extend(str(v).encode('utf-8'))
        body.extend(b'\r\n')
        
    for k, (filename, data, content_type) in files.items():
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode('utf-8'))
        body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
        body.extend(data)
        body.extend(b'\r\n')
        
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def test_ocr(image_path, label, token):
    print(f"\n=======================================================")
    print(f"--- Processing: {label} ---")
    print(f"File: {image_path}")
    with open(image_path, 'rb') as f:
        img_bytes = f.read()

    # 1. Line detection via business-api -> ai-service
    detect_res = post_multipart(
        'http://localhost:8080/api/v1/ocr/multiline/detect',
        {'privacyConfirmed': 'true'},
        {'image': (os.path.basename(image_path), img_bytes, 'image/jpeg')},
        token=token
    )
    detected_lines = detect_res.get('lines', [])
    print(f"[DETECT] Found {len(detected_lines)} candidate text lines (image size {detect_res.get('width')}x{detect_res.get('height')})")
    
    # If single-line crop without contours detected, pass full image box
    if not detected_lines:
        detected_lines = [{
            'line_id': 'line_1',
            'x': 0,
            'y': 0,
            'width': detect_res.get('width', 500),
            'height': detect_res.get('height', 50),
            'order': 1
        }]
    else:
        # Take up to 3 detected lines
        detected_lines = detected_lines[:3]

    # 2. Multiline recognition via business-api -> ai-service (CRNN best_cer.pth)
    trial_res = post_multipart(
        'http://localhost:8080/api/v1/ocr/multiline/trials',
        {
            'privacyConfirmed': 'true',
            'source': 'CAMERA',
            'confirmedLines': json.dumps(detected_lines)
        },
        {'image': (os.path.basename(image_path), img_bytes, 'image/jpeg')},
        token=token
    )
    
    trial_id = trial_res.get('trialId')
    print(f"[RECOGNIZE] Real Trial ID created in PostgreSQL: {trial_id}")
    lines = trial_res.get('lines', [])
    print(f"[RECOGNIZE] Total recognized lines: {len(lines)}")
    for idx, l in enumerate(lines):
        text_safe = l.get('predictedText', '')
        print(f"  Line {idx+1}: {text_safe} (box: {l.get('x')},{l.get('y')},{l.get('width')}x{l.get('height')})")
    return trial_res

if __name__ == '__main__':
    # 0. Authenticate
    token = login()

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_dir = os.path.join(REPO_ROOT, 'ai-training', 'handoff', 'staging', 'ocr_engine_handoff_final', 'ocr_engine', 'samples')

    # Image 1: Sample Vietnamese Handwriting 1
    sample_1 = os.path.join(samples_dir, 'sample_01.jpg')
    res1 = test_ocr(sample_1, "Image 1: Vietnamese Handwriting Sample 1", token)

    # Image 2: Sample Vietnamese Handwriting 3
    sample_3 = os.path.join(samples_dir, 'sample_03.jpg')
    res2 = test_ocr(sample_3, "Image 2: Vietnamese Handwriting Sample 3", token)

    # Image 3: Unrelated image (blank / synthetic)
    from PIL import Image
    test_unrelated = 'scratch/unrelated_test.jpg'
    os.makedirs('scratch', exist_ok=True)
    img = Image.new('RGB', (400, 100), color=(240, 240, 240))
    img.save(test_unrelated)
    res3 = test_ocr(test_unrelated, "Image 3: Completely Unrelated Image (Blank Test Image)", token)
    
    # Extract recognized texts
    text1 = " ".join([l.get('predictedText', '') for l in res1.get('lines', [])]).strip()
    text2 = " ".join([l.get('predictedText', '') for l in res2.get('lines', [])]).strip()
    text3 = " ".join([l.get('predictedText', '') for l in res3.get('lines', [])]).strip()
    
    print("\n================== VERIFICATION COMPARISON ==================")
    print(f"Image 1 Result: {text1}")
    print(f"Image 2 Result: {text2}")
    print(f"Image 3 Result: {repr(text3)}")
    print(f"Trial 1 ID: {res1.get('trialId')}")
    print(f"Trial 2 ID: {res2.get('trialId')}")
    print(f"Trial 3 ID: {res3.get('trialId')}")
    
    diff_1_2 = (text1 != text2)
    diff_1_3 = (text1 != text3)
    no_mock_text = ("Cộng hòa xã hội chủ nghĩa Việt Nam" not in text1) and \
                   ("Cộng hòa xã hội chủ nghĩa Việt Nam" not in text2) and \
                   ("Cộng hòa xã hội chủ nghĩa Việt Nam" not in text3)
    
    all_real_ids = all('-' in str(r.get('trialId')) and not str(r.get('trialId')).startswith('mock_') for r in [res1, res2, res3])

    print(f"\n[CHECK 1] Image 1 != Image 2: {diff_1_2}")
    print(f"[CHECK 2] Image 1 != Image 3: {diff_1_3}")
    print(f"[CHECK 3] No mock string ('Cộng hòa...'): {no_mock_text}")
    print(f"[CHECK 4] Real PostgreSQL UUIDs (no mock_ prefix): {all_real_ids}")

    if diff_1_2 and diff_1_3 and no_mock_text and all_real_ids:
        print("\n>>> ALL CHECKS PASSED: OCR RECOGNITION IS 100% REAL AND ACTIVE! <<<")
        sys.exit(0)
    else:
        print("\n>>> FAILED: ONE OR MORE CHECKS FAILED! <<<")
        sys.exit(1)
