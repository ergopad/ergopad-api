# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
FROM nginx/unit:1.26.1-python3.10
# FROM python:3

COPY ./app /app
WORKDIR /app

# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql nano \
  && apt-get -y install curl \
  && apt-get -y install openjdk-17-jdk \
  && apt-get -y install uvicorn \
  # && apt-get -y install gunicorn \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD tail /dev/null -f
 