import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
import psycopg2
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
TG_TOKEN = '972319967:AAHKtNOYFR8eKZfmClHURdjKpbhgdNb1C3k'

def do_start(bot: Bot, update: Update):
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Hello',
    )

def do_echo(bot: Bot, update: Update):
    text = update.message.text

    engine = create_engine('postgresql://postgres:13b1998g@localhost/postgres')
    base = declarative_base()

    class schedule(base):
        __tablename__ = 'schedule_{}'.format(text)
        id = Column(Integer, primary_key=True)
        time = Column(String)
        monday = Column(String)
        tuesday = Column(String)
        wednesday = Column(String)
        thursday = Column(String)
        friday = Column(String)
        saturday = Column(String)

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    qMonday = session.query(*[schedule.monday]).all()
    qTuesday = session.query(*[schedule.tuesday]).all()
    #filter_by(id='2')
    bot.send_message(
        chat_id=update.message.chat_id,
        text='monday : {} \n tuesday : {}'.format(qMonday, qTuesday),
    )

def main():
    bot = Bot(
        token=TG_TOKEN,
        base_url="https://telegg.ru/orig/bot",
    )
    updater= Updater(
        bot=bot,
    )
    start_handler = CommandHandler('start', do_start)
    updater.dispatcher.add_handler(start_handler)

    message_handler = MessageHandler(Filters.text, do_echo)
    updater.dispatcher.add_handler(message_handler)

    updater.start_polling()
    updater.idle()

#----------------------------database-----------------------------------------------------------------------------



#-----------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()