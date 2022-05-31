FROM python:3.9-slim-buster

SHELL ["/bin/bash", "-c"]

RUN apt update -y && apt install build-essential -y

COPY library/ /work/library/
COPY dashboard/ /work/dashboard/
WORKDIR /work/dashboard
RUN pip install -r requirements.txt

ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]