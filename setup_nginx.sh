#!/usr/bin/env bash
# Configure Nginx as a reverse proxy for the String Analytics Service.

set -euo pipefail

APP_NAME="string-analytics"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-8000}"
SERVER_NAME="${SERVER_NAME:-_}"
NGINX_CONF_DIR="/etc/nginx"
AVAILABLE_DIR="${NGINX_CONF_DIR}/sites-available"
ENABLED_DIR="${NGINX_CONF_DIR}/sites-enabled"
CONFIG_PATH="${AVAILABLE_DIR}/${APP_NAME}"
ENABLE_PATH="${ENABLED_DIR}/${APP_NAME}"

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "This script must be run as root. Try: sudo ${0}" >&2
        exit 1
    fi
}

install_nginx() {
    if ! command -v nginx >/dev/null 2>&1; then
        apt-get update
        apt-get install -y nginx
    fi
}

write_config() {
    mkdir -p "${AVAILABLE_DIR}"
    cat <<'EOF' > "${CONFIG_PATH}"
upstream string_analytics_upstream {
    server APP_HOST_PLACEHOLDER:APP_PORT_PLACEHOLDER;
    keepalive 32;
}

server {
    listen 80;
    server_name SERVER_NAME_PLACEHOLDER;

    location / {
        proxy_pass http://string_analytics_upstream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://string_analytics_upstream;
    }

    location /redoc {
        proxy_pass http://string_analytics_upstream;
    }
}
EOF

    sed -i \
        -e "s|APP_HOST_PLACEHOLDER|${APP_HOST}|g" \
        -e "s|APP_PORT_PLACEHOLDER|${APP_PORT}|g" \
        -e "s|SERVER_NAME_PLACEHOLDER|${SERVER_NAME}|g" \
        "${CONFIG_PATH}"
}

enable_site() {
    ln -sf "${CONFIG_PATH}" "${ENABLE_PATH}"
}

test_and_reload() {
    nginx -t
    systemctl reload nginx
}

main() {
    require_root
    install_nginx
    write_config
    enable_site
    test_and_reload

    cat <<EOM
Nginx configuration installed at ${CONFIG_PATH}
Proxying http://${SERVER_NAME} to ${APP_HOST}:${APP_PORT}
Ensure your FastAPI app is reachable at that address (e.g., uvicorn main:app --host ${APP_HOST} --port ${APP_PORT})
EOM
}

main "$@"
