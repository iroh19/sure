FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

# Model cache'i volume'dan kullan
ENV HF_HOME=/model-cache
# Adaptör (sure-aqua-adapter) 1B tabana göre eğitildi — taban modeli
# değiştirirsen adaptörü de yeniden eğitmen gerekir.
ENV AQUA_BASE_MODEL=KurmaAI/AQUA-1B

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
