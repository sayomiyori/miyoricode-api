#!/usr/bin/env bash
# 01a-user-key.sh
# Создание непривилегированного пользователя deploy и проброс SSH-ключа от root.
# Запускать под root.
# Идемпотентно: если пользователь deploy уже существует — шаг пропускается.

set -euo pipefail

DEPLOY_USER="deploy"
SSH_DIR="/home/${DEPLOY_USER}/.ssh"
AUTH_KEYS="${SSH_DIR}/authorized_keys"

# --- Идемпотентность -------------------------------------------------------
if id "${DEPLOY_USER}" &>/dev/null; then
    echo "Пользователь ${DEPLOY_USER} уже есть — пропускаю создание."
    exit 0
fi

# --- Создание пользователя -------------------------------------------------
useradd -m -s /bin/bash "${DEPLOY_USER}"
usermod -aG sudo "${DEPLOY_USER}"

# --- SSH-каталог и ключи ---------------------------------------------------
mkdir -p "${SSH_DIR}"
chmod 700 "${SSH_DIR}"

if [[ -f /root/.ssh/authorized_keys ]]; then
    cp /root/.ssh/authorized_keys "${AUTH_KEYS}"
else
    echo "ВНИМАНИЕ: /root/.ssh/authorized_keys не найден — authorized_keys создан пустым." >&2
    touch "${AUTH_KEYS}"
fi
chmod 600 "${AUTH_KEYS}"

chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${SSH_DIR}"
chmod 700 "/home/${DEPLOY_USER}"

echo "=== Проверь В НОВОМ терминале: ssh deploy@103.74.92.163 — должен зайти без пароля."
echo "    НЕ закрывай текущую root-сессию, пока вход не подтверждён. ==="

echo "=== 01A ГОТОВО ==="