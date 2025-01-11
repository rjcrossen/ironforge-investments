FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install python3 python3-pip -y
RUN pip3 install --upgrade pip
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
COPY ./backend /app/backend

RUN pip3 install -r requirements.txt

COPY ./main.py /app

CMD python3 main.py
