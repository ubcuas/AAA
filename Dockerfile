FROM ubcuas/pyuuas:latest

RUN apt-get -qq update && apt-get install -y

RUN mkdir -p /uas/aaa
WORKDIR /uas/aaa

COPY requirements.txt ./
RUN pip3 install -U -r requirements.txt

COPY app.py ./

EXPOSE 5000

CMD ["python", "app.py"]