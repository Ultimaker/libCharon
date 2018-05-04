# Install pytest python library as well as add all files in current directory
FROM python:alpine AS base
WORKDIR /usr/src/app
RUN apk add --no-cache git
RUN pip install --upgrade pip==9.0.*
ADD . .

# This is the container build that will run the "unit tests"
FROM base AS tests
WORKDIR /usr/src/app
RUN pip install -r requirements-testing.txt
ARG cache=1
RUN ENV_NAME=testing ASYNC_TEST_TIMEOUT=15 coverage run --source="Charon" -m pytest
RUN coverage report --skip-covered --show-missing