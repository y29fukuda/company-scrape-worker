FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py /app/
COPY scripts /app/scripts

ENTRYPOINT ["python", "worker.py"]
