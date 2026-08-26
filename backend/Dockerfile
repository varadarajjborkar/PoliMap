# PoliMap API.
#
# The image exists because this service is not a pure Python app: reading a
# photographed policy needs the Tesseract binary and its English language data,
# which no Python wheel provides. That single fact rules out the serverless
# platforms and is why the API is deployed as a container while the frontend is
# a static bundle.
#
#   docker build -f backend/Dockerfile -t polimap-api .
#   docker run -p 8000:8000 --env-file backend/.env polimap-api
#
# Build context is the repository root, not backend/, because the image needs
# datagen/ to produce the hospital corpus at build time.

FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# tesseract-ocr-eng is a separate package from tesseract-ocr on Debian, and
# without it recognition returns empty text rather than failing loudly.
#
# fonts-dejavu-core is for the printed report. The slim image ships no fonts at
# all, so without it the page falls back to Helvetica, which has no rupee glyph,
# and every figure on the document a family carries to a billing counter reads
# "Rs." while the same figure on their screen reads a rupee sign.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libglib2.0-0 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt itself
# changes, so an ordinary code change rebuilds in seconds.
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY datagen/ ./datagen/

# The hospital, procedure and insurer corpus the running app reads. Built here
# rather than committed, and --core skips rendering the policy documents, which
# only the tests and benchmarks need and which would add 80 MB to the image.
RUN python -m datagen.build_all --core

# Session rows and page images live here. Mount a volume over it to keep
# sessions across a redeploy; without one they are lost on restart, which is
# an acceptable default for state that expires in hours anyway.
VOLUME ["/app/data"]

ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/api/health')"

# Single worker on purpose. The activity stream is a long-lived SSE connection
# per session, and the event bus that feeds it is in-process, so a second
# worker would serve some browsers a stream carrying none of their own events.
# Scale by running more instances behind a load balancer with sticky sessions,
# not by adding workers here.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]