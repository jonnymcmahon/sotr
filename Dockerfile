FROM python:3

RUN apt-get update

ENV PYTHONUNBUFFERED=1

WORKDIR /django

COPY /sotr/.env /django/

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN apt-get -y install curl sudo

RUN ["curl", "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip", "-o", "awscliv2.zip"]
RUN ["unzip", "awscliv2.zip"]
RUN sudo ./aws/install