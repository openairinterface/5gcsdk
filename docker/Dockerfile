

#FROM python:3.11-slim-bullseye 
FROM ubuntu:20.04
LABEL name="UE Identity API" \
      version="V1" \
      maintainer="CAROTA Giulio <giulio.carota@eurecom.fr>" \
      io.k8s.description="ueidapi" \
      io.openshift.tags="ueidapi"

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
# Install py39 from deadsnakes repository
RUN apt-get install -y python3-pip python3.9 

COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
CMD ["python3", "app.py"] 

