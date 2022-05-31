FROM python:3.9-slim-buster

SHELL ["/bin/bash", "-c"]

RUN apt update -y && apt install build-essential -y

COPY library/ /work/library/
COPY executor/ /work/executor/
WORKDIR /work/executor/
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["main.py"]