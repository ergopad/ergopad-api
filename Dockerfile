# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
FROM python:3

COPY ./app /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql nano \
  && apt-get -y install curl openjdk-11-jdk \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/ergo-pad/ergo-python-appkit.git

CMD tail /dev/null -f
 