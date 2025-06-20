FROM debian:12-slim AS builder
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes pipx python-is-python3
ENV PATH="/root/.local/bin:${PATH}"
RUN pipx install poetry
RUN pipx inject poetry poetry-plugin-bundle
WORKDIR /src
COPY . .
RUN poetry bundle venv --python=/usr/bin/python3 --only=main /venv

FROM gcr.io/distroless/python3-debian12
COPY --from=builder /venv /venv
ENV PYTHONPATH="/venv/lib/python3.11/site-packages/"
ENTRYPOINT ["python", "/venv/lib/python3.11/site-packages/megabot/main.py"]