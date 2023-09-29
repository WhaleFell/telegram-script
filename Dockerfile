FROM python:3.8.5-alpine
COPY requirements.txt /requirements.txt
RUN apk add git &&  pip install --upgrade pip && pip install --no-cache-dir -r /requirements.txt

WORKDIR /wkdir

CMD ["python3", "main.py"]