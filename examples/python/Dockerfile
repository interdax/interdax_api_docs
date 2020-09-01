FROM python:3 as pybuild

WORKDIR /usr/src/app

RUN apt-get install ca-certificates -y
ENV WEBSOCKET_CLIENT_CA_BUNDLE=/etc/ssl/certs/ca-certificates.pem

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM pybuild

COPY . .

CMD ["python","-m","unittest"]