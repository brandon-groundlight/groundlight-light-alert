FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y \
        # We use nginx for routing requests to the correct service
        # nginx \
        # libraries required by opencv
        # libgl1-mesa-glx \
        libglib2.0-0 \
        # Some basic utilities
        curl \
        wget \
        vim \
        git \
        net-tools \
        telnet \
        alsa-utils \
        build-essential \
        # some tools for debugging
        procps htop \
        systemd \
        sudo && \
    apt-get clean

# install poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH=${POETRY_HOME}/bin:$PATH

ENV PYTHONUNBUFFERED=1

WORKDIR /opt/groundlight/gsa

# THE REAL KICKER IS HERE
COPY ./config/asound.conf /etc/asound.conf

COPY . /opt/groundlight/gsa/

RUN poetry install

CMD ["poetry", "run", "python", "app.py"]