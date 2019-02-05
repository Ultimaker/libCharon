# Install pytest python library as well as add all files in current directory
FROM python:3.4-alpine AS base
WORKDIR /usr/src/app
RUN apk add --no-cache git
ADD requirements.txt requirements.txt
ADD requirements-testing.txt requirements-testing.txt

# This is the container build that will run the "unit tests"
FROM base AS tests
WORKDIR /usr/src/app
RUN pip install -r requirements.txt
RUN pip install -r requirements-testing.txt
ARG cache=1
ADD . .
RUN ENV_NAME=testing ASYNC_TEST_TIMEOUT=15 coverage run --source="Charon" -m pytest
RUN coverage report --show-missing  --fail-under=49
