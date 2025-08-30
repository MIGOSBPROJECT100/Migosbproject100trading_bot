#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y && pkg upgrade -y
pkg install -y python git openssl libjpeg-turbo libpng
python -m pip install --upgrade pip
pip install -r requirements.txt
# Playwright browsers (Chromium) + deps
python -m playwright install chromium
echo "Install done."
