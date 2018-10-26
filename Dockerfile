FROM python:3-slim

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY main.py ./
COPY server.py ./
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "./server.py" ]
