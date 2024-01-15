import locale
import pymorphy2
import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from django.conf import settings
from bot.database_sync import get_or_create_user, create_workout, get_user_workouts, get_user_workout, \
    get_user_workout_exercises, create_exercise, get_user_exercise, get_user_exercise_sets, create_set


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')    #Установка локали на русский язык
morph = pymorphy2.MorphAnalyzer()

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')
telebot.logger.setLevel(settings.LOG_LEVEL)

user_states = {}    #Словарь для хранения состояний пользователей
user_data = {}

@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    """
    Стартовый обработчик
    :param message:
    :return:
    """
    user_id = message.from_user.id
    await get_or_create_user(user_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_create_workout = types.KeyboardButton("Создать тренировку")
    button_my_workouts = types.KeyboardButton("Мои тренировки")
    keyboard.add(button_create_workout, button_my_workouts)
    await bot.send_message(message.chat.id, "Привет! Я бот для тренировок. Выбери действие:", reply_markup=keyboard)    #Отправляем приветственное сообщение с клавиатурой


@bot.message_handler(func=lambda message: message.text == "Создать тренировку")
async def create_workout_handler(message):
    """
    Обработчик кнопки "Создать тренировку"
    """
    await bot.send_message(message.chat.id, "Введите название тренировки:")
    user_states[message.chat.id] = "waiting_for_workout_name"


@bot.message_handler(func=lambda message: message.text == "Создать упражнение")
async def create_exercise_handler(message):
    """
    Обработчик кнопки "Создать упражнение"
    """
    await bot.send_message(message.chat.id, "Введите название упражнения:")
    user_states[message.chat.id] = "waiting_for_exercise_name"


@bot.message_handler(func=lambda message: message.text == "Новый сет")
async def create_set_handler(message):
    """
    Обработчик кнопки "Новый сет"
    """
    await bot.send_message(message.chat.id, "Введите данные в формате сет вес повторений(1 2 3)")
    user_states[message.chat.id] = "waiting_for_new_set"


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


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_exercise_name")
async def process_workout_name(message):
    """
    Получение данных для создания упражнения
    :param message:
    :return:
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    exercise_name = message.text
    selected_workout = user_data[message.chat.id]
    exercise_data = {'name': exercise_name, 'workout': selected_workout}
    exercise = await create_exercise(telegram_user, exercise_data)    # Создаем упражнение и записываем в базу данных
    del user_states[message.chat.id]
    await bot.send_message(message.chat.id, f"Упражнение '{exercise.name}' создано успешно!")    #Отправляем пользователю подтверждение
    user_exercises = await get_user_workout_exercises(telegram_user, selected_workout)    #Выводим список упражнений
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if not user_exercises:
        button_create_exercise = types.KeyboardButton("Создать упражнение")
        keyboard.add(button_create_exercise)
        await bot.send_message(message.chat.id, "У вас пока нет упражнений", reply_markup=keyboard)
    else:
        button_create_exercise = types.KeyboardButton("Создать упражнение")
        keyboard.add(button_create_exercise)
        for exercise in user_exercises:
            keyboard.add(types.KeyboardButton(text=exercise.name))
        await bot.send_message(message.chat.id, "Выберите упражнение", reply_markup=keyboard)
        user_states[message.chat.id] = "waiting_for_exercise_choice"


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_new_set")
async def process_set_name(message):
    """
    Получение данных для создания сета
    :param message:
    :return:
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    values = (message.text).split()
    if len(values) != 3:
        await bot.send_message(message.chat.id, f"Неверно отправлены данные сета!")   # Возвращаем None в случае неверного формата
    else:
        set = int(values[0])    #Первое значение - количество сетов
        weight = float(values[1].replace(',', '.'))    #Второе значение - вес. Заменяем запятую на точку для правильного преобразования в float
        reps = int(values[2])    #Третье значение - количество повторений

    selected_exercise = user_data[message.chat.id]
    set_data = {'set': set, 'weight': weight, 'reps': reps, 'exercise': selected_exercise}
    set = await create_set(telegram_user, set_data)    # Создаем сет и записываем в базу данных
    del user_states[message.chat.id]
    await bot.send_message(message.chat.id, f"Cет '{set.set}' создан успешно!")    #Отправляем пользователю подтверждение
    user_sets = await get_user_exercise_sets(telegram_user, selected_exercise)    #Выводим список упражнений
    user_sets = sorted(user_sets, key=lambda x: x.date, reverse=True)[:7]  # Сортировка по дате и выбор последних 7
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_create_set = types.KeyboardButton("Новый сет")
    keyboard.add(button_create_set)
    response = "Ваши сеты \U0001F4AA:\n"
    for set in user_sets:
        formatted_date = set.date.strftime("%d")  # Форматирование даты
        month_name = morph.parse(set.date.strftime("%B"))[0].inflect({'gent'}).word  # Склонение месяца
        response += f"| Сет {set.set} | {set.weight}кг | {set.reps} повторений | {formatted_date} {month_name}\n"
    await bot.send_message(message.chat.id, response, reply_markup=keyboard)

    user_states[message.chat.id] = "waiting_for_set"


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
        user_data[message.chat.id] = selected_workout
        user_exercises = await get_user_workout_exercises(telegram_user, selected_workout)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if not user_exercises:
            button_create_exercise = types.KeyboardButton("Создать упражнение")
            keyboard.add(button_create_exercise)
            await bot.send_message(message.chat.id, "У вас пока нет упражнений", reply_markup=keyboard)
        else:
            button_create_exercise = types.KeyboardButton("Создать упражнение")
            keyboard.add(button_create_exercise)
            for exercise in user_exercises:
                keyboard.add(types.KeyboardButton(text=exercise.name))
            await bot.send_message(message.chat.id, "Выберите упражнение", reply_markup=keyboard)
            user_states[message.chat.id] = "waiting_for_exercise_choice"
    else:
        await bot.send_message(message.chat.id, f"Тренировка {selected_workout_name} не найдена.")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_exercise_choice")
async def process_exercise_choice(message):
    """
    Обработка данных выбранного упражнения
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    selected_exercise_name = message.text
    selected_exercise_data = {'name': selected_exercise_name, }
    selected_exercise = await get_user_exercise(telegram_user, name=selected_exercise_name)
    del user_states[message.chat.id]
    if selected_exercise:
        user_data[message.chat.id] = selected_exercise
        user_sets = await get_user_exercise_sets(telegram_user, selected_exercise)
        user_sets = sorted(user_sets, key=lambda x: x.date, reverse=True)[:7]    #Сортировка по дате и выбор последних 7
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if not user_sets:
            button_create_set = types.KeyboardButton("Новый сет")
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(button_create_set)
            await bot.send_message(message.chat.id, "У вас пока нет сетов в упражнении", reply_markup=keyboard)
        else:
            button_create_set = types.KeyboardButton("Новый сет")
            keyboard.add(button_create_set)
            response = "Ваши сеты \U0001F4AA:\n"
            for set in user_sets:
                formatted_date = set.date.strftime("%d")  # Форматирование даты
                month_name = morph.parse(set.date.strftime("%B"))[0].inflect({'gent'}).word    #Склонение месяца
                response += f"| Сет {set.set} | {set.weight}кг | {set.reps} повторений | {formatted_date} {month_name}\n"
            await bot.send_message(message.chat.id, response, reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id, f"Упражнение {selected_exercise_name} не найдено.")

