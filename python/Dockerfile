# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

WORKDIR /app
COPY /python/requirements.txt requirements.txt
RUN python3 -m venv /app/venv  
RUN /app/venv/bin/pip install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y \
    adduser \
    passwd \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd mercari && useradd -m -g mercari trainee
RUN chown -R trainee:mercari /app

USER trainee

EXPOSE 9000
CMD ["/bin/bash", "-c", "source /app/venv/bin/activate && python3 -m uvicorn main:app --host 0.0.0.0 --port 9000"]
#CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
