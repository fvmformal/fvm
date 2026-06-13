# TODO: we should update to debian:13, or even try to
# use alpine for faster builds

FROM debian:12-slim

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y --no-install-recommends make python3 python3-pip python3-venv bc curl ca-certificates git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# uv requires ~/.local/bin to be in your path
ENV PATH="/root/.local/bin:$PATH"
RUN uv tool install nox
