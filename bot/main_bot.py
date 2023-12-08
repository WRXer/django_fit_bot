import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from django.conf import settings
from channels.db import database_sync_to_async

from workout.models import Workout, TelegramUser

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')

telebot.logger.setLevel(settings.LOG_LEVEL)

@database_sync_to_async
def get_or_create_user(user_id):
    return TelegramUser.objects.get_or_create(telegram_id=user_id)[0]


@database_sync_to_async
def get_user_workouts(user_id):
    """
    Получение тренировок пользователя
    :param user_id:
    :return:
    """
    return list(Workout.objects.filter(user__id=user_id))


@database_sync_to_async
def create_workout(user_id, workout_data):
    """
    Создание нового объекта Тренировки
    :param user_id:
    :param workout_data:
    :return:
    """
    workout = Workout.objects.create(user=user_id, **workout_data)
    return workout

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_create_workout = types.KeyboardButton("Создать тренировку")
    button_my_workouts = types.KeyboardButton("Мои тренировки")
    keyboard.add(button_create_workout, button_my_workouts)
    # Отправляем приветственное сообщение с клавиатурой
    await bot.send_message(message.chat.id, "Привет! Я бот для тренировок. Выбери действие:", reply_markup=keyboard)



# Обработчик кнопки "Создать тренировку"
@bot.message_handler(func=lambda message: message.text == "Создать тренировку")
async def create_workout_handler(message):
    # Здесь вы можете запросить у пользователя необходимую информацию о тренировке
    # Например, использовать клавиатуру с вопросами или ждать текстового ввода

    # После получения данных о тренировке
    # Замените этот код на ваш способ получения данных о тренировке
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)

    workout_data = {
        'name': 'Тренировка 1',

        # Другие поля модели Workout
    }

    # Создаем тренировку и записываем в базу данных
    workout = await create_workout(telegram_user, workout_data)

    # Отправляем пользователю подтверждение
    await bot.send_message(message.chat.id, f"Тренировка {workout.name} создана успешно!")


# Обработчик кнопки "Мои тренировки"
@bot.message_handler(func=lambda message: message.text == "Мои тренировки")
async def my_workouts_handler(message):
    user_id = message.from_user.id
    user_workouts = await get_user_workouts(user_id)

    if not user_workouts:
        await bot.send_message(message.chat.id, "У вас пока нет тренировок.")
    else:
        workouts_text = "\n".join([f"{workout.name}" for workout in user_workouts])
        await bot.send_message(message.chat.id, f"Ваши тренировки:\n{workouts_text}")