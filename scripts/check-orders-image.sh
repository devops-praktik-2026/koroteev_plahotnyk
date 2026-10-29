#!/usr/bin/env bash
# Проверки образа 2.1. Запуск из корня проекта после сборки orders:ci.
set -euo pipefail

check_dir=$(mktemp -d)
container_id=""
cleanup() {
    if [ -n "$container_id" ]; then
        docker rm -f "$container_id" >/dev/null
    fi
    rm -rf "$check_dir"
}
trap cleanup EXIT

# Извлекаем исходный сервис целиком: его Dockerfile и контекст до изменений.
if [ -n "${BASE_REVISION:-}" ]; then
    git archive "$BASE_REVISION" services/orders | tar -x -C "$check_dir"
    docker build -t orders:before "$check_dir/services/orders"
    before=$(docker image inspect orders:before --format '{{.Size}}')
    after=$(docker image inspect orders:ci --format '{{.Size}}')
    echo "IMAGE_SIZE_BEFORE_BYTES=$before"
    echo "IMAGE_SIZE_AFTER_BYTES=$after"
fi

docker run --rm orders:ci sh -ec '
    test "$(id -u)" = 10001
    test "$(id -un)" = app
    for compiler in cc gcc g++ clang; do
        ! command -v "$compiler"
    done
    test ! -d /app/tests
    test ! -e /app/.env
    test ! -e /app/pyproject.toml
    test ! -d /build
    test -w /app
'

# Реальный запуск штатной команды контейнера и HTTP-запрос из контейнера.
container_id=$(docker run -d orders:ci)
ready=0
for attempt in $(seq 1 30); do
    if docker exec "$container_id" python -c 'import json, urllib.request; data=json.load(urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2)); assert data == {"status": "ok", "service": "orders"}' 2>/dev/null; then
        ready=1
        break
    fi
    sleep 1
done
if [ "$ready" != 1 ]; then
    docker logs "$container_id"
    exit 1
fi

# Изменяем только строку исходника в одноразовой копии контекста.
mkdir "$check_dir/changed"
cp -a services/orders/. "$check_dir/changed/"
printf '\n# Проверка кеширования зависимостей.\n' >> "$check_dir/changed/orders/main.py"
docker build --progress=plain -t orders:cache-check "$check_dir/changed" 2>&1 | tee "$check_dir/cache.log"
python3 - "$check_dir/cache.log" <<'PY'
import pathlib
import re
import sys

log = pathlib.Path(sys.argv[1]).read_text()
steps = re.findall(r"^(#\d+) \[dependencies [^\]]+\] RUN python -m venv", log, re.M)
if not steps or not any(f"{step} CACHED" in log for step in steps):
    raise SystemExit("Слой установки зависимостей не взят из кеша")
print("DEPENDENCIES_CACHED_AFTER_SOURCE_CHANGE=yes")
PY
echo 'IMAGE_CHECKS=passed: non-root, no compiler, minimal files, health, dependency cache'
