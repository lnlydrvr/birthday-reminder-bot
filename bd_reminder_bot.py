import os
import sqlite3
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
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
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    date_of_birth TEXT NOT NULL,
    added_by_admin INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, chat_id)
)
''')
conn.commit()

MONTHS_TRANSLATION = {
    'January': 'января', 'February': 'февраля', 'March': 'марта', 'April': 'апреля',
    'May': 'мая', 'June': 'июня', 'July': 'июля', 'August': 'августа',
    'September': 'сентября', 'October': 'октября', 'November': 'ноября', 'December': 'декабря'
}

def format_date_russian(date):
    day = date.strftime("%d")
    month = date.strftime("%B")  # Получаем название месяца на английском
    return f"{day} {MONTHS_TRANSLATION[month]}"

# Функция для проверки прав администратора
async def is_admin(chat_id, user_id):
    admins = await client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
    return any(admin.id == user_id for admin in admins)

# Функция удаления сообщений через 2 минуты
async def delete_message_later(event, message):
    await asyncio.sleep(60)
    await client.delete_messages(event.chat_id, [event.message.id, message.id])

# Команда /start
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    message = await event.respond("Привет! Я бот, который напоминает о днях рождениях. 🎊\n"
                                  "\n"
                                  "Вот мои команды для всех пользователей:\n"
                                  "‣ /user_add ДД-ММ-ГГГГ - добавить свой день рождения\n"
                                  "‣ /list - вывести весь список дней рождений\n"
                                  "\n"
                                  "Команды для администраторов:\n"
                                  "‣ /admin_add @username ДД-ММ-ГГГГ - добавить день рождения пользователя\n"
                                  "‣ /admin_delete @username - удалить день рождения пользователя")
    asyncio.create_task(delete_message_later(event, message))

# Команда для добавления дня рождения пользователем
@client.on(events.NewMessage(pattern='/user_add'))
async def add_birthday(event):
    args = event.message.text.split()
    if len(args) != 2:
        message = await event.respond("ℹ️ Использование: /user_add ДД-ММ-ГГГГ")
        asyncio.create_task(delete_message_later(event, message))
        return
    
    date_str = args[1]
    try:
        date_of_birth = format_date_russian(datetime.strptime(date_str, "%d-%m-%Y"))
    except ValueError:
        message = await event.respond("❌ Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
        asyncio.create_task(delete_message_later(event, message))
        return
    
    cursor.execute('''INSERT OR REPLACE INTO birthdays (user_id, chat_id, username, first_name, last_name, date_of_birth, added_by_admin)
                      VALUES (?, ?, ?, ?, ?, ?, 0)''', (event.sender_id, event.chat_id, event.sender.username, event.sender.first_name, event.sender.last_name, date_of_birth))
    conn.commit()
    message = await event.respond(f"✅ Ваш день рождения добавлен: {date_of_birth}.")
    asyncio.create_task(delete_message_later(event, message))

# Команда для просмотра списка дней рождений
@client.on(events.NewMessage(pattern='/list'))
async def list_birthdays(event):
    cursor.execute('SELECT first_name, last_name, date_of_birth FROM birthdays WHERE chat_id = ? ORDER BY strftime("%m %d", date_of_birth)', (event.chat_id,))
    users = cursor.fetchall()
    
    if not users:
        message = await event.respond("Нет записанных дней рождений. 😥")
    else:
        message = "🗓️ Дни рождения участников чата:\n \n"
        for user in users:
            first_name, last_name, date_of_birth = user
            last_name_text = f" {last_name}" if last_name else ""
            message += f"{first_name}{last_name_text} - {date_of_birth}\n"
        message = await event.respond(message)
    
    asyncio.create_task(delete_message_later(event, message))

# Команда для добавления дня рождения администратором
@client.on(events.NewMessage(pattern='/admin_add'))
async def add_user_birthday(event):
    if not await is_admin(event.chat_id, event.sender_id):
        message = await event.respond("❌ У вас нет прав администратора.")
        asyncio.create_task(delete_message_later(event, message))
        return
    
    args = event.message.text.split()
    if len(args) != 3:
        message = await event.respond("ℹ️ Использование: /admin_add @username ДД-ММ-ГГГГ")
        asyncio.create_task(delete_message_later(event, message))
        return
    
    username, date_str = args[1], args[2]
    try:
        date_of_birth = format_date_russian(datetime.strptime(date_str, "%d-%m-%Y"))
    except ValueError:
        message = await event.respond("❌ Неверный формат даты. Используйте ДД-ММ-ГГГГ.")
        asyncio.create_task(delete_message_later(event, message))
        return
    
    user = await client.get_entity(username)
    cursor.execute('''INSERT OR REPLACE INTO birthdays (user_id, chat_id, username, first_name, last_name, date_of_birth, added_by_admin)
                      VALUES (?, ?, ?, ?, ?, ?, 1)''', (user.id, event.chat_id, username, user.first_name, user.last_name, date_of_birth))
    conn.commit()
    message = await event.respond(f"✅ День рождения {user.first_name} добавлен: {date_of_birth}.")
    asyncio.create_task(delete_message_later(event, message))
    
# Команда для удаления дня рождения администратором
@client.on(events.NewMessage(pattern='/admin_delete'))
async def remove_user_birthday(event):
    if not await is_admin(event.chat_id, event.sender_id):
       message = await event.respond("❌ У вас нет прав администратора.")
       asyncio.create_task(delete_message_later(event, message))
       return
    
    args = event.message.text.split()
    if len(args) != 2:
        message = await event.respond("ℹ️ Использование: /admin_delete @username")
        asyncio.create_task(delete_message_later(event, message))
        return
    
    username = args[1]
    user = await client.get_entity(username)
    cursor.execute('DELETE FROM birthdays WHERE user_id = ? AND chat_id = ?', (user.id, event.chat_id))
    conn.commit()
    message = await event.respond(f"✅ День рождения {user.first_name} удалён.")
    asyncio.create_task(delete_message_later(event, message))

# Отправка напоминания о дне рождении
async def birthday_reminder():
    while True:
        now = datetime.now()

        if now.hour == 6 and now.minute == 30:
            today = now.strftime("%d %B").lower()
            cursor.execute('SELECT chat_id, username FROM birthdays WHERE date_of_birth = ?', (today,))
            users = cursor.fetchall()

            for chat_id, username in users:
                await client.send_message(chat_id, f"Сегодня день рождения у @{username}! \n Поздравляем! 🎉")

        await asyncio.sleep(60)

# Запуск бота
async def main():
    asyncio.create_task(birthday_reminder())
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())