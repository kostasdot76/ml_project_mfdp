FROM python:3.11-slim

WORKDIR /app

# Копируем CLIP из локальной папки
COPY ./clip /app/clip

COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt && \
    pip install dvc dvc-s3

RUN pip install /app/clip

EXPOSE 8080

CMD ["python", "api.py"]



