FROM registry.woden.us.es/containers/questa:2025.1_2

RUN yum install -y git python39 java-1.8.0-openjdk
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# uv requires ~/.local/bin to be in your path
ENV PATH="/root/.local/bin:$PATH"
ENV SALT_LICENSE_SERVER=29000@popote.us.es
RUN uv tool install nox
