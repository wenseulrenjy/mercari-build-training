# syntax=docker/dockerfile:1
FROM alpine:latest

RUN apk add --no-cache python3 py3-pip py3-virtualenv

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN python3 -m venv ./venv && \
    ./venv/bin/activate && \
    pip install -r requirements.txt

COPY . .

RUN addgroup -S mercari && adduser -S trainee -G mercari
RUN chown -R trainee:mercari ./db
RUN chown -R trainee:mercari ./images

USER trainee

CMD ["/venv/bin/uvicorn", "main:app","--host", "0.0.0.0", "--reload", "--port", "9000"]