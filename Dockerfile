FROM python:3.13

WORKDIR /app
COPY . .

RUN bash /app/locales.sh
RUN pip install --root-user-action ignore --no-cache-dir -r requirements.txt
RUN touch /app/birthdays.db && chmod 666 /app/birthdays.db

EXPOSE 8443

ENTRYPOINT ["python", "-u", "bd_reminder_bot.py"]
