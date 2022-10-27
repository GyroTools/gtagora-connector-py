FROM python:3.9
COPY . /src
WORKDIR /src
RUN python setup.py install