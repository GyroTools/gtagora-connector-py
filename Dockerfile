FROM python:3.7
COPY . /src
WORKDIR /src
RUN python setup.py install