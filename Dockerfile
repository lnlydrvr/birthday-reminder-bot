FROM python:3.13
COPY . /app
WORKDIR /app
RUN pip install --root-user-action ignore -r requirements.txt 
RUN touch /app/birthdays.db
EXPOSE 8443
ENTRYPOINT ["python"]
CMD ["bd_reminder_bot.py"]