FROM python:3.9-slim-buster

WORKDIR /work
SHELL ["/bin/bash", "-c"]

COPY *.py library/ /work/

RUN apt update -y && apt install build-essential -y
RUN pip install -r requirements.txt

ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]