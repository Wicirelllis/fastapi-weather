FROM python:3.12.10-slim-bookworm

WORKDIR /app

COPY ./requirements.txt /

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

