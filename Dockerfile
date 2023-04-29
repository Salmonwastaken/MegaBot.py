FROM python:3.11.3-alpine3.17

WORKDIR /app

ENV PYTHONUNBUFFERED 1

RUN apk add git --no-cache

COPY requirements.txt .
RUN pip3 install -r requirements.txt && rm requirements.txt

COPY app .

CMD ["python3", "main.py"]