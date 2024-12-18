import os
import sqlite3
import asyncio
from datetime import datetime, time
from dotenv import load_dotenv
from telethon import TelegramClient, events
import locale

# Устанавливаем локализацию на русский язык (убрана для Docker)
# locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

# Загрузка конфигурации из .env файла
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация клиента
client = TelegramClient('birthday_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Подключение к базе данных SQLite
conn = sqlite3.connect('birthdays.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для хранения дней рождений
cursor.execute('''
CREATE TABLE IF NOT EXISTS birthdays (
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT,
    date_of_birth TEXT NOT NULL,
    PRIMARY KEY (user_id, chat_id)
)
''')
conn.commit()

# Словарь для хранения состояний пользователей
user_states = {}

# Словарь с названиями месяцев и их числовыми значениями
MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}

# Функция для преобразования даты в числовой формат для сортировки
def date_to_sort_key(date):
    day, month = date.split()
    return (MONTHS[month], int(day))

# Запуск бота
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Привет! Я бот-напоминалка о днях рождениях. Используй команду /add для добавления дня рождения.")

# Инициализация процесса записи дня рождения
@client.on(events.NewMessage(pattern='/add'))
async def add_birthday(event):
    user_states[event.sender_id] = 'awaiting_date'
    await event.respond("Пожалуйста, введите дату рождения в формате ДД-ММ-ГГГГ:")

# Отмена процесса записи дня рождения
@client.on(events.NewMessage(pattern='/cancel'))
async def cancel(event):
    if event.sender_id in user_states and user_states[event.sender_id] == 'awaiting_date':
        del user_states[event.sender_id]
        await event.respond("Добавление дня рождения отменено.")
    else:
        await event.respond("Нет активной операции добавления дня рождения.")

# Запись дня рождения в базу данных
@client.on(events.NewMessage)
async def handle_date_input(event):
    if event.sender_id in user_states and user_states[event.sender_id] == 'awaiting_date':
        if event.message.text.startswith('/'):
            return

        date_str = event.message.text

        try:
            date_of_birth = datetime.strptime(date_str, "%d-%m-%Y")
            formatted_date = date_of_birth.strftime("%d %B").lower()

            first_name = event.sender.first_name
            last_name = event.sender.last_name if event.sender.last_name else None
            username = event.sender.username if event.sender.username else None

            cursor.execute('''
                INSERT OR REPLACE INTO birthdays (user_id, chat_id, username, first_name, last_name, date_of_birth)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event.sender_id, event.chat_id, username, first_name, last_name, formatted_date))
            conn.commit()

            del user_states[event.sender_id]
            last_name_text = f" {last_name}" if last_name else ""
            await event.respond(f"День рождения добавлен для {first_name}{last_name_text}: {formatted_date}.")
        except ValueError:
            await event.respond("Неверный формат даты. Используйте формат ДД-ММ-ГГГГ.")

# Отправка напоминания о дне рождении
async def birthday_reminder():
    while True:
        now = datetime.now()

        if now.time() >= time(8, 30) and now.time() < time(8, 31):
            today = now.strftime("%d %B").lower()
            cursor.execute('SELECT chat_id, username FROM birthdays WHERE date_of_birth = ?', (today,))
            users = cursor.fetchall()

            for chat_id, username in users:
                await client.send_message(chat_id, f"Сегодня день рождения у @{username}! Поздравляем! 🎉")

        await asyncio.sleep(60)

# Вывод всех записанных дней рождений
@client.on(events.NewMessage(pattern='/list'))
async def list_birthdays(event):
    cursor.execute('SELECT first_name, last_name, date_of_birth FROM birthdays WHERE chat_id = ?', (event.chat_id,))
    users = cursor.fetchall()

    if not users:
        await event.respond("Нет записанных дней рождений.")
    else:
        # Сортировка с использованием функции date_to_sort_key
        sorted_users = sorted(users, key=lambda x: date_to_sort_key(x[2]))

        # Формирование сообщения
        message = "Дни рождения:\n"
        for user in sorted_users:
            first_name, last_name, date_of_birth = user
            last_name_text = f" {last_name}" if last_name else ""
            message += f"{first_name}{last_name_text} - {date_of_birth}\n"
        
        await event.respond(message)

# Запуск задачи напоминания о днях рождения
async def main():
    asyncio.create_task(birthday_reminder())
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
