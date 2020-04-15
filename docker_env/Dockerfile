FROM registry.hub.docker.com/library/debian:buster-slim

RUN apt-get update && apt-get -y install cmake make python3 python3-pip git

COPY docker_env/buildenv_check.sh buildenv_check.sh

COPY charon_requirements.txt charon_requirements.txt

RUN pip3 install -r charon_requirements.txt
