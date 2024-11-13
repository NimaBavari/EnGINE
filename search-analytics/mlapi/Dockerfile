FROM python:3.10.7-slim

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5070

CMD gunicorn -w 4 -b 0.0.0.0:5070 main:app
