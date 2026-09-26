FROM ubuntu:latest
LABEL authors="dorbi"

ENTRYPOINT ["top", "-b"]