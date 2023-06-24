FROM fluxrm/flux-sched:focal
# docker build -t flux-burst -f examples/Dockerfile .
# docker run -it flux-burst -f examples/Dockerfile
USER root
ENV PATH=/opt/conda:/bin:$PATH
WORKDIR /code
COPY . /code
RUN pip install -e . && \
    ln -s /bin/python3 /usr/local/bin/python
USER fluxuser
