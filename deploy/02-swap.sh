#!/usr/bin/env bash
# 02-swap.sh
# Настройка swap 2G + vm.swappiness=10 для VPS 1 CPU / 2 GB RAM.
# Идемпотентен: повторный запуск безопасен.

set -euo pipefail

SWAP_FILE="/swapfile"
SWAP_SIZE="2G"
FSTAB_LINE="${SWAP_FILE} none swap sw 0 0"
SYSCTL_KEY="vm.swappiness"
SYSCTL_VALUE="10"

# --- Идемпотентность: если swap уже есть ---------------------------------
if [[ -f "${SWAP_FILE}" ]]; then
    echo "swap уже настроен (${SWAP_FILE} существует) — пропускаю."
    free -h
    exit 0
fi

# --- Создание swapfile ----------------------------------------------------
if command -v fallocate &>/dev/null; then
    fallocate -l "${SWAP_SIZE}" "${SWAP_FILE}"
else
    # fallback: dd (fallocate отсутствует в некоторых минимальных образах)
    dd if=/dev/zero of="${SWAP_FILE}" bs=1M count=2048 status=progress
fi

chmod 600 "${SWAP_FILE}"
mkswap "${SWAP_FILE}"
swapon "${SWAP_FILE}"

# --- /etc/fstab (проверка дубликата) --------------------------------------
if ! grep -qE "^[[:space:]]*${SWAP_FILE}[[:space:]]" /etc/fstab; then
    printf "%s\n" "${FSTAB_LINE}" >> /etc/fstab
fi

# --- vm.swappiness (идемпотентно) -----------------------------------------
if grep -qE "^[[:space:]]*${SYSCTL_KEY}[[:space:]]*=" /etc/sysctl.conf; then
    sed -i -E "s|^[[:space:]]*${SYSCTL_KEY}[[:space:]]*=.*|${SYSCTL_KEY}=${SYSCTL_VALUE}|" /etc/sysctl.conf
else
    printf "\n%s=%s\n" "${SYSCTL_KEY}" "${SYSCTL_VALUE}" >> /etc/sysctl.conf
fi
sysctl -p

# --- Проверка -------------------------------------------------------------
free -h

echo "=== 02 ГОТОВО ==="