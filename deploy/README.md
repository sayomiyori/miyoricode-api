# Server Hardening — Ubuntu VPS 103.74.92.163

Скрипты для защиты SSH-периметра коммерческого сервера:
создание непривилегированного пользователя `deploy`, закрытие root-входа по SSH,
установка UFW + fail2ban, установка Docker.

## ⚠️ Предупреждение

> **Шаг 3 (`01b-ssh-hardening.sh`) закрывает root по SSH навсегда.**
> Если шаг 2 не пройден (вход под `deploy` не подтверждён в отдельном терминале),
> вы потеряете доступ к серверу. Физический/консольный доступ (или KVM/IPMI)
> понадобится для восстановления.

Все скрипты идемпотентны — повторный запуск безопасен.

## Порядок выполнения

1. **Под root, в текущей сессии:**
   ```bash
   sudo bash 01a-user-key.sh
   ```

2. **В НОВОМ терминале** (текущую root-сессию НЕ закрывать!):
   ```bash
   ssh deploy@103.74.92.163
   ```
   Должен зайти без пароля по ключу.
   Подтвердить вход — без этого шаг 3 выполнять **нельзя**.

3. **Под `deploy` через `sudo`:**
   ```bash
   sudo bash 01b-ssh-hardening.sh
   ```
   После этого шага root-вход по SSH закрыт навсегда.

4. **Под `deploy` через `sudo`:**
   ```bash
   sudo bash 01c-docker.sh
   ```

## Что делает каждый скрипт

| Файл | Назначение |
|------|------------|
| `01a-user-key.sh` | Создаёт пользователя `deploy`, добавляет в `sudo`, пробрасывает `authorized_keys` от root. Идемпотентен. |
| `01b-ssh-hardening.sh` | `PermitRootLogin no`, `PasswordAuthentication no`, валидация `sshd -t`, UFW (22/80/443), fail2ban (`maxretry=4`, `bantime=1h`). |
| `01c-docker.sh` | Docker Engine + compose plugin через `get.docker.com`, `deploy` в группу `docker`. |

## Что в конце каждого скрипта

- `01a` — просьба проверить вход под `deploy` в новом терминале.
- `01b` — `fail2ban-client status sshd` + `ufw status verbose`.
- `01c` — `docker version` + `docker compose version`.

## Откат (если что-то пошло не так)

Физический/консольный доступ → залогиниться под `deploy` или через rescue-режим:

```bash
sed -i 's/^PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sshd -t && systemctl restart sshd
```