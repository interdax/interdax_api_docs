FROM python:3 as pybuild

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM pybuild

COPY . .

CMD ["python","-m","unittest"]