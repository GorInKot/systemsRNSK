#!/usr/bin/env bash
# Копирует токенизированные бланки в backend, откуда их использует сервис заполнения заявок.
# Запускать после `python3 build/build.py`, если поменялись оригиналы бланков в types/.
set -euo pipefail
cd "$(dirname "$0")/.."
cp build/tokenized/*.xlsx build/tokenized/*.docx backend/app/data/templates/
echo "Шаблоны скопированы в backend/app/data/templates/"
