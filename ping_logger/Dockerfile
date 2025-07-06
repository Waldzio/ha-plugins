FROM python:3.11-alpine

RUN pip install pythonping paho-mqtt

COPY ping_logger.py /ping_logger.py
CMD [ "python", "/ping_logger.py" ]