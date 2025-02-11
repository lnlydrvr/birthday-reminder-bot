#!/bin/bash

# Обновление списка пакетов и установка locales
apt-get update && apt-get install -y locales

# Генерация локали ru_RU.UTF-8
locale-gen ru_RU.UTF-8

# Установка локали для всех параметров
update-locale \
    LANG=ru_RU.UTF-8 \
    LANGUAGE=ru_RU.UTF-8 \
    LC_CTYPE=ru_RU.UTF-8 \
    LC_NUMERIC=ru_RU.UTF-8 \
    LC_TIME=ru_RU.UTF-8 \
    LC_COLLATE=ru_RU.UTF-8 \
    LC_MONETARY=ru_RU.UTF-8 \
    LC_MESSAGES=ru_RU.UTF-8 \
    LC_PAPER=ru_RU.UTF-8 \
    LC_NAME=ru_RU.UTF-8 \
    LC_ADDRESS=ru_RU.UTF-8 \
    LC_TELEPHONE=ru_RU.UTF-8 \
    LC_MEASUREMENT=ru_RU.UTF-8 \
    LC_IDENTIFICATION=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

# Применение изменений
export LANG=ru_RU.UTF-8
export LANGUAGE=ru_RU.UTF-8
export LC_TIME=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8

echo "Все параметры локали успешно настроены:"
locale
