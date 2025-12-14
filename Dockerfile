FROM python:3.14.2-slim

ENV PYTHONUNBUFFERED=1
ENV DENO_INSTALL=/

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg curl unzip && apt-get clean

RUN curl -fsSL https://deno.land/install.sh | sh

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src .

EXPOSE 8000
