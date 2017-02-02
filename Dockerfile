FROM python:3.6-alpine

EXPOSE 9999/udp
WORKDIR /srv
ADD . /srv
RUN pip install -q -r /srv/requirements.txt
CMD ["/srv/run.py"]

