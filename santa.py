import telebot
from telebot import types
from peewee import Model, SqliteDatabase, CharField, BooleanField, IntegrityError
import random

TOKEN = ""
bot = telebot.TeleBot(TOKEN)

admin_user_id = "1702825309"  # Замените этот ID на фактический ID вашего пользователя

# Инициализация базы данных SQLite
db = SqliteDatabase('applications.db')

# Определение модели для пользователей
class User(Model):
    user_id = CharField(unique=True)
    has_application = BooleanField(default=False)
    application_sent = BooleanField(default=False)

    class Meta:
        database = db

# Определение модели для заявлений
class Application(Model):
    user = CharField()
    name = CharField()
    message = CharField()

    class Meta:
        database = db

# Создаем таблицы в базе данных
db.connect()
db.create_tables([User, Application])

# Добавляем переменную для хранения состояния рассылки
broadcast_user_id = None

# Команда /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_hello = types.KeyboardButton(text="Ереже")
    button_list = types.KeyboardButton(text="Қатысушылар Тізімі")
    button_application = types.KeyboardButton(text="Тіркелу")
    button_admin = types.KeyboardButton(text="")
    markup.row(button_hello, button_list, button_application)
    markup.row(button_admin)

    bot.send_message(message.chat.id, "💬 Әрине ойнағысы  Тіркелу    ал қатыспайтын адамдарды мәжбүрлемейміз!\n---------------------------------------------------------------------------------\n❗ШАРТ!\nШАТАСПАУ ҮШІН ЕСІМІҢІЗДІ ЖӘНЕ СЫНЫБЫҢЫЗДЫ ЖАЗЫП КЕТІҢІЗ ЕГЕР ОЛАЙ ЖАСАМАСАНЫЗ ТІЗІМНЕН ЖОЙЫЛАСЫЗ\n---------------------------------------------------------------------------------\n🔁ҚАТЫСҚАН АДАМ ШЫҒА АЛМАЙДЫ ШЫҚҚЫСЫ КЕЛЕТІНДЕР @connect102 ЖАЗАМЫЗ\n---------------------------------------------------------------------------------\n✅Бұл бот жәй көніл көтеріп оқушылар арасындағы қарым қатынасты дамытады Кез келген оқушы кез келген оқушымен түседі.Ойын басталатын уақытта ADMIN хабарлайды әзірше тіркелу болып жатыр \n---------------------------------------------------------------------------------\n❤️Өтінемін ешкімді алдауды ойламайақ  тек өзіміз үшін қатысуларыңызды өтінемін!\nТүсінбей жатсаныз 👨‍💻 @connect102", reply_markup=markup)

# Команда /hello
@bot.message_handler(func=lambda message: message.text == 'Ереже')
def handle_hello(message):
    bot.send_message(message.chat.id, "ЕРЕЖЕ!\n🎉Ойын барысында қатысушылар тіркеледі. Тіркелген қатысушылар жинақталғанда бот ойынды бастайды. Бот сізге 1 адамның есімін береді. Ол қыз болуы мүмкін немесе ұлда болуы мүмкін, осылай барлық адамға тізім ішінен адам тауып береді. Еш бір адам сыйлықсыз қалмайды деген үміттемін. Бұның бәрі сіз кімге түстініз соған байланысты және сізге байланысты. Сізге бот силық беретін адамды шығарып береді және сіз сол адамға кез келген сыйлық дауындайсыз. Солай сізгеде 1 адам дауындайды. Ендеше СӘТТІЛІК!🎁 ")

@bot.message_handler(func=lambda message: message.text == 'Қатысушылар Тізімі')
def handle_list(message):
    applications = Application.select()
    if applications:
        response = "ҚАТЫСУШЫЛАР:\n"
        for app in applications:
            response += f"{app.message}\n"
    else:
        response = "Қатысушылар әзірге жоқ."

    if response:  # Проверяем, что response не пустой
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Жоқ пайдаланушылар табылмады.")

# Команда /admin
@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if str(message.chat.id) == admin_user_id:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_random = types.KeyboardButton(text="/random")
        button_broadcast = types.KeyboardButton(text="Рассылка")
        markup.row(button_random)
        markup.row(button_broadcast)

        bot.send_message(message.chat.id, "ADMIN панелге кош келдін.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Сен админ емессін админ тек Елдос Рауф.")

# Команда /random
@bot.message_handler(commands=['random'])
def handle_random(message):
    if str(message.chat.id) == admin_user_id:
        users = list(User.select().where(User.application_sent == True))

        if len(users) < 2:
            bot.send_message(message.chat.id, "ен кемі 2 адам қажет.")
            return

        random.shuffle(users)

        for i in range(len(users)):
            user = users[i]
            receiver = users[(i + 1) % len(users)]
            receiver_name = Application.get(Application.user == receiver.user_id).name
            bot.send_message(user.user_id, f"Сіздің силық беретін адамыңыз: {receiver_name}")

        bot.send_message(message.chat.id, "Ал енді қандай силық беретініңді асыға күтеміз .")
    else:
        bot.send_message(message.chat.id, "Сен Админ емессін админ Елдос Рауф")

# Команда /broadcast
@bot.message_handler(func=lambda message: message.text == 'Рассылка')
def handle_broadcast(message):
    global broadcast_user_id

    # Проверяем, что отправитель команды - администратор
    if str(message.chat.id) == admin_user_id:
        broadcast_user_id = str(message.chat.id)
        bot.send_message(message.chat.id, "Жіберілетін сөз немесе фотоны жіберініз:")
        bot.register_next_step_handler(message, process_broadcast_input)
    else:
        bot.send_message(message.chat.id, "Сіз админ емессіз.")

# Обработчик следующего шага для ввода текста или изображения рассылки
def process_broadcast_input(message):
    global broadcast_user_id

    # Проверяем, что рассылку запрашивал администратор
    if str(message.chat.id) == admin_user_id and broadcast_user_id:
        users = list(User.select().where(User.application_sent == True))
        
        if users:
            if message.text:
                text = message.text.strip()  # Убираем лишние пробелы в начале и конце текста
                admin_broadcast_message = f"*АДМИН\n* {text}"
                for user in users:
                    bot.send_message(user.user_id, admin_broadcast_message, parse_mode='Markdown')
            elif message.photo:
                # Если отправлено изображение, отправляем его всем пользователям
                for user in users:
                    bot.send_photo(user.user_id, message.photo[0].file_id)
            else:
                bot.send_message(admin_user_id, "Текст немесе Фото Оқылмай жатыр.")
                return

            bot.send_message(admin_user_id, "Сәтті жіберілді.")
            broadcast_user_id = None
        else:
            bot.send_message(admin_user_id, "Собщения баратн адам жоқ.")
    else:
        bot.send_message(admin_user_id, "Сіз админ емессіз немесе дұрыс жазбадыңыз.")



# Обработка нажатия на кнопку "Заявление"
@bot.message_handler(func=lambda message: message.text == 'Тіркелу')
def handle_application_button(message):
    user_id = str(message.chat.id)
    try:
        existing_user = User.create(user_id=user_id)
    except IntegrityError:
        existing_user = User.get(user_id=user_id)

    if existing_user.has_application:
        bot.send_message(message.chat.id, "Сіз тіркеліп қойдыныз басқа тіркеле алмайсыз")
    elif existing_user.application_sent:
        bot.send_message(message.chat.id, "Сіз тіркеліп қойдыныз басқа тіркеле алмайсыз 2ншрет тіркеле алмайсыз.")
    else:
        bot.send_message(message.chat.id, "Аты жөніңіз сыныбыңыз Міндетті ары қарай қысқа сөз жазсаныз болады.")
        existing_user.has_application = True
        existing_user.save()

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message(message):
    user_id = str(message.chat.id)

    try:
        user = User.get(user_id=user_id)
    except User.DoesNotExist:
        # Если пользователя не существует, отправляем ему сообщение о том, что нужно сначала воспользоваться кнопкой "Тіркелу"
        bot.send_message(message.chat.id, "")
        return

    if user.has_application and not user.application_sent:
        # Добавление заявления в базу данных
        application = Application.create(user=user_id, name=message.text, message=message.text)
        bot.send_message(message.chat.id, f"{message.text} Тізімге қосылды.")
        user.application_sent = True  # Устанавливаем флаг отправки заявления
        user.save()
    else:
        bot.send_message(message.chat.id, "")


# Остальной код оставляем без изменений
if __name__ == '__main__':
    bot.polling(none_stop=True)
