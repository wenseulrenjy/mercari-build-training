# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

WORKDIR /app

RUN python -m venv .app/venv

RUN source .app/venv/bin/activate

RUN pip install --upgrade pip setuptools wheel

COPY  requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "uvicorn", "main:app" , "--reload", "--port 9000"]
