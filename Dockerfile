FROM python:3.13-slim

WORKDIR /app

COPY source/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt

COPY source/app.py ./app.py
COPY source/datetime.txt ./datetime.txt

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://0.0.0.0:5000/alive')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
