FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/app/.cache/huggingface OMP_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false PORT=7860
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
RUN useradd -m -u 1000 appuser && chown appuser:appuser /app
COPY --chown=appuser:appuser . .
USER appuser
RUN python -m scripts.preparar_modelo
EXPOSE 7860
CMD ["sh", "-c", "exec gunicorn wsgi:app --bind 0.0.0.0:${PORT:-7860} --workers 1 --threads 4 --timeout 300 --access-logfile -"]
