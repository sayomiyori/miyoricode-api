#!/usr/bin/env bash
# 01c-docker.sh
# Установка Docker Engine + docker compose plugin через официальный скрипт.
# Добавление deploy в группу docker.

set -euo pipefail

DEPLOY_USER="deploy"

# --- Docker Engine ---------------------------------------------------------
if ! command -v docker &>/dev/null; then
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    rm -f /tmp/get-docker.sh
fi

# --- Права для deploy ------------------------------------------------------
if id "${DEPLOY_USER}" &>/dev/null; then
    usermod -aG docker "${DEPLOY_USER}"
fi

docker version
docker compose version

echo "=== 01C ГОТОВО ==="