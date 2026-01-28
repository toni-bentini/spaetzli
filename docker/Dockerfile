# Spaetzli Docker Image
# Rotki with embedded premium mock server

# ============ Build mock server ============
FROM python:3.11-slim AS mock-build

WORKDIR /mock
COPY spaetzli_mock_server/ ./spaetzli_mock_server/

RUN pip install --no-cache-dir fastapi uvicorn python-multipart && \
    pip install --no-cache-dir --target=/mock/deps fastapi uvicorn python-multipart

# ============ Build patched Rotki ============
FROM --platform=$BUILDPLATFORM node:22-bookworm AS frontend-build-stage

ARG BUILDARCH
ENV CYPRESS_INSTALL_BINARY=0
ENV NODE_OPTIONS="--max-old-space-size=4096"

WORKDIR /app
COPY rotki/frontend/ .
RUN if [ "$BUILDARCH" != "amd64" ]; then \
      apt-get update && \
      apt-get install -y build-essential python3 --no-install-recommends; \
    fi && \
    npm install -g corepack@latest && \
    corepack enable && \
    pnpm install --frozen-lockfile && \
    pnpm run docker:build

FROM rust:1-bookworm AS colibri-build-stage

WORKDIR /app
COPY rotki/colibri/ ./colibri
RUN cargo build --target-dir /tmp/dist/colibri --manifest-path ./colibri/Cargo.toml --release

FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS backend-build-stage

ARG TARGETARCH
ARG ROTKI_VERSION=1.41.3
ENV PACKAGE_FALLBACK_VERSION=$ROTKI_VERSION
ARG PYINSTALLER_VERSION=v6.15.0

WORKDIR /app
COPY rotki/pyproject.toml rotki/uv.lock* ./

RUN uv sync --locked --no-dev --no-install-project

COPY rotki/ /app

# Apply Spaetzli patch
COPY scripts/apply_patch.py /tmp/
RUN python /tmp/apply_patch.py /app/rotkehlchen/premium/premium.py

RUN sed "s/fallback_version.*/fallback_version = \"$PACKAGE_FALLBACK_VERSION\"/" -i pyproject.toml && \
    uv sync --locked --no-dev --no-install-project && \
    if [ "$TARGETARCH" != "amd64" ]; then \
      git clone https://github.com/pyinstaller/pyinstaller.git && \
      cd pyinstaller && git checkout ${PYINSTALLER_VERSION} && \
      cd bootloader && ./waf all && cd .. && \
      uv pip install "pyinstaller @ ."; \
    else \
      uv pip install pyinstaller==${PYINSTALLER_VERSION}; \
    fi && \
    cd /app && \
    uv pip install -e . && \
    uv run python -c "import sys;from rotkehlchen.db.misc import detect_sqlcipher_version; version = detect_sqlcipher_version();sys.exit(0) if version == 4 else sys.exit(1)" && \
    PYTHONOPTIMIZE=2 uv run pyinstaller --noconfirm --clean --distpath /tmp/dist rotkehlchen.spec

# ============ Runtime image ============
FROM nginx:1.26 AS runtime

LABEL maintainer="Spaetzli"

ARG ROTKI_VERSION=1.41.3
ENV ROTKI_VERSION=$ROTKI_VERSION
ENV SPAETZLI_MOCK_URL=http://127.0.0.1:18090

RUN apt-get update && \
    apt-get install -y procps python3 python3-pip curl --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy mock server
COPY --from=mock-build /mock/spaetzli_mock_server /opt/spaetzli/spaetzli_mock_server
COPY --from=mock-build /mock/deps /opt/spaetzli/deps

# Copy Rotki
COPY --from=backend-build-stage /tmp/dist /opt/rotki
COPY --from=colibri-build-stage /tmp/dist/colibri/release/colibri /opt/rotki
COPY --from=frontend-build-stage /app/app/dist /opt/rotki/frontend

RUN APP=$(find "/opt/rotki" -name "rotki-core-*-linux" | head -n 1) && \
    echo "${APP}" && \
    ln -s "${APP}" /usr/sbin/rotki && \
    ln -s /opt/rotki/colibri /usr/sbin/colibri

VOLUME ["/data", "/logs", "/config"]

EXPOSE 80

COPY rotki/packaging/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.py /opt/rotki/entrypoint.py

CMD ["python3", "/opt/rotki/entrypoint.py"]

HEALTHCHECK CMD ["curl", "--fail", "http://localhost/api/1/ping"]
