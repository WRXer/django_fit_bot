import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from django.conf import settings
from bot.database_sync import get_or_create_user, create_workout, get_user_workouts


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

    workout_data = {
        'name': workout_name,
    }

    # Создаем тренировку и записываем в базу данных
    workout = await create_workout(telegram_user, workout_data)
    del user_states[message.chat.id]

    # Отправляем пользователю подтверждение
    await bot.send_message(message.chat.id, f"Тренировка '{workout.name}' создана успешно!")


# Обработчик кнопки "Мои тренировки"
@bot.message_handler(func=lambda message: message.text == "Мои тренировки")
async def my_workouts_handler(message):
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)

    user_workouts = await get_user_workouts(telegram_user)

    if not user_workouts:
        await bot.send_message(message.chat.id, "У вас пока нет тренировок.")
    else:
        workouts_text = "\n".join([f"{workout.name}" for workout in user_workouts])
        await bot.send_message(message.chat.id, f"Ваши тренировки:\n{workouts_text}")
