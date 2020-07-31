FROM python:3.8-slim-buster
SHELL ["/bin/bash", "-c"]
ENV SLACK_WEBHOOK="https://hooks.slack.com/services/XXX/YYYY/ZZZZZ"
EXPOSE 3300
WORKDIR /work
ADD *.py /work/
ADD requirements.txt /work/
ADD templates/ /work/
ADD static/ /work/
RUN pip install -r requirements.txt
ENTRYPOINT python app.py
