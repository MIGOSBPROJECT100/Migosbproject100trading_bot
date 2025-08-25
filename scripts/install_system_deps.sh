#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git
# Playwright deps
sudo apt-get install -y libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 libcups2 libxrandr2 \
    libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libdrm2 libgbm1 libasound2 libatspi2.0-0 libxkbcommon0
