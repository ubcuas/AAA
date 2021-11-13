FROM ubcuas/pyuuas:latest

RUN apt-get -qq update && apt-get install -y

RUN mkdir -p /uas/aaa
WORKDIR /uas/aaa

COPY src/requirements.txt ./src/
RUN pip3 install -r src/requirements.txt

COPY src/ ./src/

CMD ["python", "src/tests/test_avoidance.py"]