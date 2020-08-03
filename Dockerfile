FROM python:3.7-slim-buster
SHELL ["/bin/bash", "-c"]
ENV SLACK_WEBHOOK="https://hooks.slack.com/services/XXX/YYYY/ZZZZZ"
ENV HOSTS_PATH="hosts.yaml"
ENV MODE="develop"
EXPOSE 3301
WORKDIR /work
RUN apt update -y && apt install build-essential -y
ADD requirements.txt /work/
RUN pip install -r requirements.txt
RUN pip install uwsgi
ADD *.py /work/
ADD templates/ /work/templates/
ADD static/ /work/static/
# ENTRYPOINT python app.py
ENTRYPOINT uwsgi --http :3301 --wsgi-file app.py --callable app
