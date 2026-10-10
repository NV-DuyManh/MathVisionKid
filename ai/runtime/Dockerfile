FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    RUNTIME_MODE=MODEL \
    OCR_PROVIDER=crnn_vi_handwriting_v1 \
    OCR_DEVICE=cpu \
    CANONICAL_RUNTIME_OVERRIDE_ENABLED=false \
    PORT=8000

# OpenCV/Ultralytics require these shared libraries on the slim Linux image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Keep the tested pins, but install CPU wheels before the general requirements.
RUN sed -n -e '/^torch==/p' -e '/^torchvision==/p' requirements.txt > /tmp/torch-cpu.txt \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu -r /tmp/torch-cpu.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && rm /tmp/torch-cpu.txt

RUN groupadd --system mathvision \
    && useradd --system --gid mathvision --create-home mathvision \
    && mkdir -p /app/models /home/mathvision/.config/Ultralytics \
    && chown mathvision:mathvision /app/models /home/mathvision/.config /home/mathvision/.config/Ultralytics

# Models are supplied through a read-only /app/models volume at deployment time.
COPY --chown=mathvision:mathvision app ./app

USER mathvision
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=5)"

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
