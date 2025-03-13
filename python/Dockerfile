# syntax=docker/dockerfile:1
FROM alpine

RUN apk add --no-cache python3 py3-pip

WORKDIR /app
COPY . /python/requirements.txt requirements.txt
RUN python3 -m venv /app/venv && \
    . /app/venv/bin/activate && \
    pip install -r requirements.txt

COPY . .

RUN addgroup -S mercari && adduser -S trainee -G mercari
RUN chown -R trainee:mercari /app/python/db
RUN chown -R trainee:mercari /app/python/images

USER trainee

CMD ["/app/venv/bin/uvicorn", "python.main:app","--host", "0.0.0.0", "--reload", "--port", "9000"]