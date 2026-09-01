#!/usr/bin/env bash
# 01b-ssh-hardening.sh
# ЗАПУСКАТЬ ТОЛЬКО после подтверждённого входа как deploy по ключу в отдельном терминале.
# Закрывает root-вход по SSH, отключает пароли, настраивает ufw + fail2ban.

set -euo pipefail

SSHD_CONFIG="/etc/ssh/sshd_config"
JAIL_LOCAL="/etc/fail2ban/jail.local"

# --- Идемпотентная правка sshd_config -------------------------------------
# Ищем существующую директиву (после возможных пробелов и ; в начале строки);
# если есть — заменяем значение, если нет — дописываем в конец.

upsert_sshd_directive() {
    local key="$1"
    local value="$2"
    # Совпадение: начало строки, пробелы или ';' (закомментированная), затем ключ,
    # затем пробелы и текущее значение до конца строки.
    if grep -qE "^[[:space:]]*;?[[:space:]]*${key}[[:space:]]" "${SSHD_CONFIG}"; then
        sed -i -E "s|^[[:space:]]*;?[[:space:]]*${key}[[:space:]].*|${key} ${value}|" "${SSHD_CONFIG}"
    else
        printf "\n%s %s\n" "${key}" "${value}" >> "${SSHD_CONFIG}"
    fi
}

upsert_sshd_directive "PermitRootLogin" "no"
upsert_sshd_directive "PasswordAuthentication" "no"
upsert_sshd_directive "PubkeyAuthentication" "yes"

# --- Валидация конфигурации перед перезапуском ----------------------------
if ! sshd -t; then
    echo "ОШИБКА: sshd -t завершился с ненулевым кодом — конфигурация НЕ валидна." >&2
    echo "Перезапуск sshd НЕ выполнен. Проверь ${SSHD_CONFIG} вручную." >&2
    exit 1
fi

systemctl restart sshd

# --- UFW -------------------------------------------------------------------
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# --- fail2ban --------------------------------------------------------------
if ! dpkg -s fail2ban &>/dev/null; then
    apt-get update
    apt-get install -y fail2ban
fi

cat > "${JAIL_LOCAL}" <<'EOF'
[sshd]
enabled = true
maxretry = 4
bantime = 1h
backend = systemd
EOF

systemctl enable --now fail2ban

# --- Верификация -----------------------------------------------------------
fail2ban-client status sshd || true
ufw status verbose || true

echo "=== 01B ГОТОВО ==="