import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
import psycopg2
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import apiai
import json
import math

DialogFlow_TELEBOT_API_TOKEN = '58395c6273454d75a68116451c2002b6'
DialogFlow_SMALLTALK_API_TOKEN = "368f30714cb54bf499df02386bce9729"
TG_TOKEN_BOT = '972319967:AAHKtNOYFR8eKZfmClHURdjKpbhgdNb1C3k'

user_hero_db = 'nvlchrlzijfvsk'
name_hero_db = 'd6ub309hbsvm8'
psw_hero_db = 'e5d6b2abd2ee59f765e8f4499f97b0970dbd98d0a4f7532c5131483196d90812'
host_hero_db = 'ec2-54-246-92-116.eu-west-1.compute.amazonaws.com'
#ACCESS_TO_HEROKU_DB = 'postgresql://{}:{}@{}:5432/{}'.format(user_hero_db, psw_hero_db, host_hero_db, name_hero_db)
ACCESS_TO_HEROKU_DB = 'postgres://nvlchrlzijfvsk:e5d6b2abd2ee59f765e8f4499f97b0970dbd98d0a4f7532c5131483196d90812@ec2-54-246-92-116.eu-west-1.compute.amazonaws.com:5432/d6ub309hbsvm8'
ACCESS_TO_LOCAL_DB = 'postgresql://postgres:13b1998g@localhost/postgres'

GLOBAL_LIST = []
def send_message_dflow(message):#работа с dialogflow
    request = apiai.ApiAI(DialogFlow_TELEBOT_API_TOKEN).text_request()#подключиилсь к пользовательскому dialogflow и собираемся отправить ему запрос
    request.lang = 'ru'
    request.session_id = 'session_1'
    request.query = message #кладем в запрос текс сообщения ползователя
    response = json.loads(request.getresponse().read().decode('utf-8'))
    return response

def do_start(bot: Bot, update: Update):#настройки команды бота /start
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Привет, напиши номер группы и я покажу все пары этой группы в понедельник',
    )

def weekday_list(sch,k):
    return [sch[k].monday, sch[k].tuesday, sch[k].wednesday, sch[k].thursday, sch[k].friday, sch[k].saturday]

def get_result_shedule(sch):
    wdays = [[], [], [], [], [], []]
    k=0
    while len(sch) > k:
        l=0
        while l < 6:
            wd_l = weekday_list(sch, k)
            if not (wd_l[l] is None):
                wdays[l].append('{}. '.format(k+1) + sch[k].time + ' ' + wd_l[l])
            l = l + 1
        k=k+1
    l=0
    ans_l = []
    ans = ''
    while l < len(wdays):
        k=0
        while k < len(wdays[l]):
            ans = ans + wdays[l][k] + '; '
            k = k + 1
        ans_l.append(ans)
        l = l + 1
        ans = ''

    return ans_l

def get_info_from_db(num_of_group, weekdays : list):
    engine = create_engine(ACCESS_TO_LOCAL_DB)
    base = declarative_base()

    class schedule(base):#создание таблицы для получения информации из базы данных
        __tablename__ = '{}'.format(num_of_group)
        id = Column(Integer, primary_key=True)
        time = Column(String)
        monday = Column(String)
        tuesday = Column(String)
        wednesday = Column(String)
        thursday = Column(String)
        friday = Column(String)
        saturday = Column(String)

    base.metadata.create_all(engine)  # бд
    session = sessionmaker(bind=engine)()  # бд

    sch = session.query(*[schedule]).all()  # получения всей информации из колонки понедельник таблицы бд
    days = get_result_shedule(sch)

    days_of_week =['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота']
    week_dict = {'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3, 'пятница': 4, 'суббота': 5}
    if len(weekdays)==0 or len(weekdays)==6:
        weekdays = days_of_week
    k = 0
    ans = ''
    while k < len(weekdays):
        ans = ans + str(weekdays[k]) + ': ' + days[week_dict[weekdays[k]]] + '\n'
        k = k + 1

    return ans

def get_par_df(response_dialog_flow):
    specifically = response_dialog_flow['result']['parameters']['specifically']
    num = response_dialog_flow['result']['parameters']['number']
    whom = response_dialog_flow['result']['parameters']['whom']
    wd = response_dialog_flow['result']['parameters']['weekday']
    wd1 = response_dialog_flow['result']['parameters']['weekday1']
    wd2 = response_dialog_flow['result']['parameters']['weekday2']
    wd3 = response_dialog_flow['result']['parameters']['weekday3']
    wd4 = response_dialog_flow['result']['parameters']['weekday4']
    wd5 = response_dialog_flow['result']['parameters']['weekday5']
    wds_fir = [wd, wd1, wd2, wd3, wd4, wd5]
    wds = [i for i in wds_fir if i !='']
    return [specifically, num, whom, wds]

def send_message(bot: Bot, update: Update, bot_answer):
    bot.send_message(
        chat_id=update.message.chat_id,
        text=bot_answer,
    )

def do_answer(bot: Bot, update: Update): #updater : Updater):#бот читает новое сообщение и отвечает на него обратившись сначала к бд
    global GLOBAL_LIST
    text = update.message.text#чтение сообщение пользователя
    response_dialog_flow = send_message_dflow(text)#отправляю сообщение пользователя на dialogflow

    if (response_dialog_flow['result']['action'] == 'question_along_a_schedule' and \
            response_dialog_flow['result']['parameters']['specifically'] != '' and \
            response_dialog_flow['result']['parameters']['whom'] != '') or GLOBAL_LIST != []:

        if GLOBAL_LIST == []:
            par_df = get_par_df(response_dialog_flow)
            specifically, num, whom, weekdays = par_df[0], par_df[1], par_df[2], par_df[3]
            if whom != 'деканат' and num == '':  # если это студенты и они не указали группу, передаем информацию глобальному контексту отпарвляем смс и занаво пускаем бота
                GLOBAL_LIST = par_df
                bot_answer = 'напиши номер группы - 6 цифр'
            else:   # если все впорядке-номер группы есть обращаемся к бд
                table_name = whom + '_' + num
                bot_answer = get_info_from_db(table_name, weekdays)

        else:
            specifically, num, whom, weekdays = GLOBAL_LIST[0], GLOBAL_LIST[1], GLOBAL_LIST[2], GLOBAL_LIST[3]
            num = response_dialog_flow['result']['parameters']['number']
            if len(num) == 6:
                GLOBAL_LIST = []
                table_name = whom + '_' + num
                bot_answer = get_info_from_db(table_name, weekdays)
            else:
                bot_answer = response_dialog_flow['result']['fulfillment']['speech']

    else:
        bot_answer = response_dialog_flow['result']['fulfillment']['speech']

    send_message(bot, update, bot_answer)

def main():
    bot = Bot(  # создание бота
        token=TG_TOKEN_BOT,
        base_url="https://telegg.ru/orig/bot",
    )
    updater = Updater(
        bot=bot,
    )
    start_handler = CommandHandler('start', do_start)  # загрузиил команду
    updater.dispatcher.add_handler(start_handler)  # добавили команду боту

    message_handler = MessageHandler(Filters.text, do_answer)  # загрузиил ответы
    updater.dispatcher.add_handler(message_handler)  # добавили ответы боту

    updater.start_polling()
    updater.idle()

while True:
    main()
