FROM python:3.9
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN python setup.py install