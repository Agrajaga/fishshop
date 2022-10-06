# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster
WORKDIR /bot_app
COPY requirements.txt /bot_app/
RUN pip3 install --no-cache-dir -r requirements.txt
COPY .env .
COPY shop_api.py .
COPY tg_bot.py .
CMD ["python3", "tg_bot.py"]