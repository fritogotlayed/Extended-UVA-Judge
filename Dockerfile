FROM alpine:3.6

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    rm -r /root/.cache

COPY . /judge

WORKDIR /judge

RUN pip install -e .

# Open Port
EXPOSE 80

# Use this if you want bash
# ENTRYPOINT ["/bin/bash"]

ENTRYPOINT ["extended-uva-judge-server"]