import locale
import pymorphy2
import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from django.conf import settings
from bot.database_sync import get_or_create_user, create_workout, get_user_workouts, get_user_workout, \
    get_user_workout_exercises, create_exercise, get_user_exercise, get_user_exercise_sets, create_set, \
    create_workout_filter

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')    #Установка локали на русский язык
morph = pymorphy2.MorphAnalyzer()

bot = AsyncTeleBot(settings.TOKEN_BOT, parse_mode='HTML')
telebot.logger.setLevel(settings.LOG_LEVEL)

user_states = {}    #Словарь для хранения состояний пользователей
user_data = {}
user_back = {}


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


@bot.message_handler(func=lambda message: message.text == "Назад")
async def back_button_handler(message):
    """
    Обработчик кнопки "Назад"
    """
    if user_back.get(message.chat.id) == "main_menu":
        await send_welcome(message)
    elif user_back.get(message.chat.id) == "workout_menu":
        await my_workouts_handler(message)
    elif user_back.get(message.chat.id) == "exercise_menu":
        #message = user_back[message.chat.id]
        await my_workouts_handler(message)
        #await process_workout_choice(message)


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
    await bot.send_message(message.chat.id, "Введите данные в формате: сет вес повторений(1 2 3)")
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
    user_workouts = await create_workout_filter(telegram_user, workout_data)
    if not user_workouts:
        workout = await create_workout(telegram_user, workout_data)    # Создаем тренировку и записываем в базу данных
        await bot.send_message(message.chat.id, f"Тренировка '{workout.name}' создана успешно!")    #Отправляем пользователю подтверждение
        await my_workouts_handler(message)
    else:
        await bot.send_message(message.chat.id, f"Тренировка '{workout_name}' не создана! Такое имя уже используется!")

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
        await bot.send_message(message.chat.id, f"Неверно отправлены данные сета!")   #Возвращаем None в случае неверного формата
    else:
        set_c = int(values[0])    #Первое значение - количество сетов
        weight = float(values[1].replace(',', '.'))    #Второе значение - вес. Заменяем запятую на точку для правильного преобразования в float
        reps = int(values[2])    #Третье значение - количество повторений
        selected_exercise = user_data[message.chat.id]
        set_data = {'set': set_c, 'weight': weight, 'reps': reps, 'exercise': selected_exercise}
        created_set = await create_set(telegram_user, set_data)    #Создаем сет и записываем в базу данных
        del user_states[message.chat.id]
        await bot.send_message(message.chat.id, f"Cет {created_set.set} | {created_set.weight} кг | {created_set.reps} повторений добавлен!")    #Отправляем пользователю подтверждение
        user_sets = await get_user_exercise_sets(telegram_user, selected_exercise)    #Выводим список упражнений
        user_sets = sorted(user_sets, key=lambda x: x.date, reverse=True)    #Получаем даты сетов
        unique_dates = []
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_create_set = types.KeyboardButton("Новый сет")
        button_back = types.KeyboardButton("Назад")
        user_back[message.chat.id] = "exercise_menu"
        keyboard.add(button_create_set, button_back)
        for one_set in user_sets:
            formatted_date = one_set.date.strftime("%d")    #Форматирование даты
            month_name = morph.parse(one_set.date.strftime(" %B"))[0].inflect({'gent'}).word    #Склонение месяца
            day_month_key = one_set.date.strftime("%d%m")
            if day_month_key not in unique_dates:    #Проверяем, есть ли уже дата в списке
                unique_dates.append(day_month_key)
                button = types.KeyboardButton(formatted_date + month_name)
                keyboard.add(button)
        await bot.send_message(message.chat.id, "Выберите дату для просмотра сетов в этот день", reply_markup=keyboard)
    user_states[message.chat.id] = "waiting_for_set_choice"


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
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if not user_workouts:
        button_back = types.KeyboardButton("Назад")
        user_back[message.chat.id] = "main_menu"
        keyboard.add(button_back)
        await bot.send_message(message.chat.id, "У вас пока нет тренировок.", reply_markup=keyboard)
    else:
        button_back = types.KeyboardButton("Назад")
        user_back[message.chat.id] = "main_menu"
        keyboard.add(button_back)
        for workout in user_workouts:
            keyboard.add(types.KeyboardButton(text=workout.name))
        await bot.send_message(message.chat.id, "Выберите тренировку", reply_markup=keyboard)
        user_states[message.chat.id] = "waiting_for_workout_choice"


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_workout_choice")
async def process_workout_choice(message):
    """
    Обработка данных выбранной тренировки
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    selected_workout_name = message.text
    selected_workout = await get_user_workout(telegram_user, name=selected_workout_name)
    if selected_workout:
        user_exercises = await get_user_workout_exercises(telegram_user, selected_workout)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if not user_exercises:
            button_create_exercise = types.KeyboardButton("Создать упражнение")
            button_back = types.KeyboardButton("Назад")
            user_back[message.chat.id] = "workout_menu"
            user_data[message.chat.id] = selected_workout_name
            keyboard.add(button_create_exercise, button_back)
            await bot.send_message(message.chat.id, "У вас пока нет упражнений", reply_markup=keyboard)
        else:
            button_create_exercise = types.KeyboardButton("Создать упражнение")
            button_back = types.KeyboardButton("Назад")
            user_back[message.chat.id] = "workout_menu"
            user_data[message.chat.id] = selected_workout_name
            keyboard.add(button_create_exercise, button_back)
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
    selected_exercise = await get_user_exercise(telegram_user, name=selected_exercise_name)
    if selected_exercise:
        user_data[message.chat.id] = selected_exercise
        user_sets = await get_user_exercise_sets(telegram_user, selected_exercise)
        user_sets = sorted(user_sets, key=lambda x: x.date, reverse=True)
        if not user_sets:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button_create_set = types.KeyboardButton("Новый сет")
            button_back = types.KeyboardButton("Назад")
            user_back[message.chat.id] = "exercise_menu"
            keyboard.add(button_create_set, button_back)
            await bot.send_message(message.chat.id, "У вас пока нет сетов в упражнении", reply_markup=keyboard)
        else:
            unique_dates = []
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button_create_set = types.KeyboardButton("Новый сет")
            button_back = types.KeyboardButton("Назад")
            user_back[message.chat.id] = "exercise_menu"
            keyboard.add(button_create_set, button_back)
            for one_set in user_sets:
                formatted_date = one_set.date.strftime("%d")    #Форматирование даты
                month_name = morph.parse(one_set.date.strftime(" %B"))[0].inflect({'gent'}).word    #Склонение месяца
                day_month_key = one_set.date.strftime("%d%m")
                if day_month_key not in unique_dates:    #Проверяем, есть ли уже дата в множестве
                    unique_dates.append(day_month_key)
                    button = types.KeyboardButton(formatted_date + month_name)
                    keyboard.add(button)
            await bot.send_message(message.chat.id, "Выберите дату выполнения сета", reply_markup=keyboard)
            user_states[message.chat.id] = "waiting_for_set_choice"
    else:
        await bot.send_message(message.chat.id, f"Упражнение {selected_exercise_name} не найдено.")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_set_choice")
async def process_set_date(message):
    """
    Обработка данных выбранного сета
    """
    user_id = message.from_user.id
    telegram_user = await get_or_create_user(user_id)
    selected_exercise = user_data[message.chat.id]
    selected_date_str = message.text
    response_text = f"Сеты от {selected_date_str}:\n"
    user_sets = await get_user_exercise_sets(telegram_user, selected_exercise)
    for one_set in user_sets:
        formatted_date = one_set.date.strftime("%d")    #Форматирование даты
        month_name = morph.parse(one_set.date.strftime(" %B"))[0].inflect({'gent'}).word    #Склонение месяца
        format_set_date = formatted_date + month_name
        if selected_date_str == format_set_date:
            response_text += f"Сет {one_set.set} | {one_set.weight}кг | {one_set.reps} повторений |\n"
    await bot.send_message(message.chat.id, response_text)


