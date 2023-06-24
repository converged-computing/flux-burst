FROM ubuntu

# docker build -t flux-burst .

LABEL MAINTAINER @vsoch
ENV PATH /opt/conda/bin:${PATH}
ENV LANG C.UTF-8
RUN apt-get update && \
    apt-get install -y wget vim && \
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

WORKDIR /code
COPY . /code
RUN pip install -e .[all] && pip install ipython
