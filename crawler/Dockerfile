FROM python:3.9-slim-buster

SHELL ["/bin/bash", "-c"]

RUN apt update -y && apt install build-essential -y

COPY library/ /work/library/
COPY crawler/ /work/crawler/
WORKDIR /work/crawler/
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["main.py"]