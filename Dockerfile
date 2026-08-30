FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CPU wheel first. A default PyPI torch install pulls CUDA/nvidia-* (several GB).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# only-if-needed keeps the CPU torch already installed so sentence-transformers
# cannot replace it with the CUDA build from PyPI.
RUN pip install --no-cache-dir --upgrade-strategy only-if-needed -r requirements.txt \
    && python -c "import torch; assert '+cpu' in torch.__version__, torch.__version__"

COPY app ./app

ENV HF_HOME=/root/.cache/huggingface
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
