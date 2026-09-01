# Nginx reverse-proxy — FastAPI на VPS

Установка и активация конфига `miyoricode-api.conf` для проксирования
`103-74-92-163.nip.io → 127.0.0.1:8000` (Docker-контейнер с FastAPI).

## Зачем отдельный конфиг для /chat

Эндпоинт `POST /chat` отдаёт ответ через `StreamingResponse` (Server-Sent Events).
На Render стрим **дважды** ломался: nginx-слой Render-а буферизировал SSE,
в результате клиент получал `Content-Length: 0` и пустое тело — ассистент
«зависал» без ошибок.

В этом конфиге директивы против буферизации вынесены **только** в
`location = /chat`:

- `proxy_buffering off;`
- `proxy_cache off;`
- `proxy_read_timeout 3600s;`
- `proxy_set_header Connection '';`
- `add_header X-Accel-Buffering no always;`
- `chunked_transfer_encoding on;`

Остальные эндпоинты (`/health`, REST JSON, `/docs`, `/openapi.json` и т.п.)
остаются под **дефолтной** буферизацией nginx — для маленьких JSON-ответов
это снижает количество syscalls и улучшает латентность.

> ⚠️ **Не переносить SSE-директивы на уровень `server` или в `location /`.**
> Глобальное отключение буферизации убьёт производительность обычных API.

## Предусловия

- Docker-контейнер с FastAPI запущен и слушает `127.0.0.1:8000`
  (проверка: `curl -sS http://127.0.0.1:8000/health` отвечает 200).
- DNS для `103-74-92-163.nip.io` уже резолвится в `103.74.92.163`
  (nip.io делает это автоматически, но проверить: `dig +short 103-74-92-163.nip.io`).
- Пользователь `deploy` имеет sudo-доступ (см. `deploy/README.md` → шаг 3).
- UFW открыт: `sudo ufw allow 80/tcp` и `sudo ufw allow 443/tcp`
  (если ещё не открывали в `01b-ssh-hardening.sh`).
- Nginx установлен: `sudo apt install -y nginx`.

## Порядок действий

> ⚠️ **`sudo nginx -t` перед reload — ОБЯЗАТЕЛЬНО.**
> Битый конфиг = nginx откажется стартовать и положит весь reverse-proxy
> (включая будущий HTTPS). Команда `-t` проверяет синтаксис без затрагивания
> рабочего процесса и подскажет строку с ошибкой.

### 1. Скопировать конфиг в sites-available

```bash
sudo cp deploy/nginx/miyoricode-api.conf /etc/nginx/sites-available/
```

### 2. Активировать через symlink в sites-enabled

```bash
sudo ln -s /etc/nginx/sites-available/miyoricode-api.conf /etc/nginx/sites-enabled/
```

Если в `/etc/nginx/sites-enabled/` уже есть `default` — его лучше убрать,
иначе он перехватит запросы раньше нашего server-блока:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

### 3. Проверить синтаксис

```bash
sudo nginx -t
```

Ожидаемый вывод:

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Если ошибка — **не** переходить к reload. Вернуться к редактированию конфига,
исправить, повторить шаг 3.

### 4. Применить конфиг

```bash
sudo systemctl reload nginx
```

Без перезапуска процесса — `reload` подхватывает новый конфинг и не рвёт
текущие соединения.

### 5. Smoke-тест: обычный эндпоинт

```bash
curl -sS http://103-74-92-163.nip.io/health
```

Должен вернуть 200 и тело от FastAPI (а не HTML-страницу nginx по умолчанию).

### 6. Smoke-тест: SSE-стрим

```bash
curl -N -X POST http://103-74-92-163.nip.io/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"ping"}'
```

Ожидаемое поведение:

- В ответе видны события SSE (строки `data: ...`) по мере генерации, **без**
  ожидания полной готовности ответа.
- В `curl` работает флаг `-N` (no-buffer), иначе он сам буферизирует вывод.

Для сравнения можно дополнительно проверить заголовки:

```bash
curl -sS -D - -o /dev/null -X POST http://103-74-92-163.nip.io/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"ping"}'
```

В выводе должны присутствовать:

```
Transfer-Encoding: chunked
X-Accel-Buffering: no
```

`Content-Length` **должен отсутствовать** — для SSE длина тела заранее неизвестна.

## Добавление HTTPS (certbot)

> ⚠️ **Запускать certbot ПОСЛЕ успешного reload nginx (шаг 4) и ПОСЛЕ
> прохождения smoke-тестов.** Certbot модифицирует конфиг, добавляя
> `listen 443 ssl;` и блок для редиректа 80→443. Если на шаге 4 был баг —
> certbot его «зацементирует».

```bash
sudo certbot --nginx -d 103-74-92-163.nip.io
```

Certbot:

1. Получит сертификат через HTTP-01 challenge (нужен открытый порт 80).
2. Модифицирует `/etc/nginx/sites-available/miyoricode-api.conf`:
   добавит `listen 443 ssl;`, пути к сертификатам и блок `location /`
   с редиректом на HTTPS. **Структуру `location = /chat` он не трогает**,
   но стоит перечитать итоговый файл после.
3. Предложит добавить редирект 80→443 (рекомендуется `2 — Redirect`).

После certbot повторить:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

И проверить HTTPS-версию smoke-тестов, заменив `http://` на `https://`.

Автопродление сертификата (`certbot renew`) уже настроен через systemd-timer
в Ubuntu, дополнительных действий не требуется.

## Откат

Если новый конфиг сломал reverse-proxy:

```bash
sudo rm /etc/nginx/sites-enabled/miyoricode-api.conf
sudo systemctl reload nginx
```

Nginx вернётся к конфигурации, которая была до активации symlink-а
(либо к `default`, если он остался в `sites-enabled/`).

## Чек-лист

- [ ] `curl http://127.0.0.1:8000/health` → 200
- [ ] `sudo cp deploy/nginx/miyoricode-api.conf /etc/nginx/sites-available/`
- [ ] `sudo ln -s /etc/nginx/sites-available/miyoricode-api.conf /etc/nginx/sites-enabled/`
- [ ] Старый `default` убран из `sites-enabled/`
- [ ] `sudo nginx -t` → `test is successful`
- [ ] `sudo systemctl reload nginx` без ошибок
- [ ] `curl http://103-74-92-163.nip.io/health` → 200
- [ ] `curl -N -X POST http://103-74-92-163.nip.io/chat ...` → SSE-события видны в реальном времени
- [ ] В заголовках ответа `/chat` есть `X-Accel-Buffering: no` и `Transfer-Encoding: chunked`
- [ ] `sudo certbot --nginx -d 103-74-92-163.nip.io` (после всех проверок выше)
- [ ] HTTPS smoke-тесты после certbot