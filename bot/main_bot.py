import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from django.conf import settings
from bot.database_sync import get_or_create_user, create_workout, get_user_workouts, get_user_workout

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')
telebot.logger.setLevel(settings.LOG_LEVEL)

user_states = {}    #Словарь для хранения состояний пользователей

@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    """
    Стартовый обработчик
    :param message:
    :return:
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_create_workout = types.KeyboardButton("Создать тренировку")
    button_my_workouts = types.KeyboardButton("Мои тренировки")
    keyboard.add(button_create_workout, button_my_workouts)
    await bot.send_message(message.chat.id, "Привет! Я бот для тренировок. Выбери действие:", reply_markup=keyboard)    #Отправляем приветственное сообщение с клавиатурой



@bot.message_handler(func=lambda message: message.text == "Создать тренировку")
async def create_workout_handler(message):
    """
    Обработчик кнопки "Создать тренировку"
    Здесь вы можете запросить у пользователя необходимую информацию о тренировке
    Например, использовать клавиатуру с вопросами или ждать текстового ввода
    """
    await bot.send_message(message.chat.id, "Введите название тренировки:")
    user_states[message.chat.id] = "waiting_for_workout_name"


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_workout_name")
async def process_workout_name(message):
    """
    Получение данных для создания тренировки
    :param message:
    :return:
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    workout_name = message.text
    workout_data = {'name': workout_name,}
    workout = await create_workout(telegram_user, workout_data)    # Создаем тренировку и записываем в базу данных
    del user_states[message.chat.id]
    await bot.send_message(message.chat.id, f"Тренировка '{workout.name}' создана успешно!")    #Отправляем пользователю подтверждение


@bot.message_handler(func=lambda message: message.text == "Мои тренировки")
async def my_workouts_handler(message):
    """
    Обработчик кнопки "Мои тренировки"
    :param message:
    :return:
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    user_workouts = await get_user_workouts(telegram_user)
    if not user_workouts:
        await bot.send_message(message.chat.id, "У вас пока нет тренировок.")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for workout in user_workouts:
            markup.add(types.KeyboardButton(text=workout.name))
        await bot.send_message(message.chat.id, "Выберите тренировку", reply_markup=markup)
        user_states[message.chat.id] = "waiting_for_workout_choice"


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_workout_choice")
async def process_workout_choice(message):
    """
    Обработка данных выбранной тренировки
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    selected_workout_name = message.text
    selected_workout_data = {'name': selected_workout_name, }
    selected_workout = await get_user_workout(telegram_user, name=selected_workout_name)
    del user_states[message.chat.id]

    if selected_workout:
        await bot.send_message(message.chat.id, f"Выбрана тренировка: {selected_workout.name}")
    else:
        await bot.send_message(message.chat.id, f"Тренировка {selected_workout_name} не найдена.")




