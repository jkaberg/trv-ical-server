FROM python:3-slim

ENV TRV_DEBUG=False

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY main.py ./
COPY server.py ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD [ "python", "./server.py" ]
