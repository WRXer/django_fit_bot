FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR app/

COPY requirements.txt .

RUN apt-get update && apt-get install -y python3-dev

RUN apt-get update \
    && apt-get install -y locales \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8

RUN pip install --no-cache-dir -r requirements.txt

COPY . .