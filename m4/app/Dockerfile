FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt && \
    pip install dvc dvc-s3

EXPOSE 8080

CMD ["python", "api.py"]



