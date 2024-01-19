from channels.db import database_sync_to_async
from workout.models import Workout, TelegramUser, Exercise, Sets


@database_sync_to_async
def get_or_create_user(user_id):
    """
    Получение или создалние пользователя
    :param user_id:
    :return:
    """
    return TelegramUser.objects.get_or_create(telegram_id=user_id)[0]


@database_sync_to_async
def get_user_workouts(user_id):
    """
    Получение тренировок пользователя
    :param user_id:
    :return:
    """
    return list(Workout.objects.filter(user=user_id))


@database_sync_to_async
def create_workout(user_id, workout_data):
    """
    Создание нового объекта Тренировки
    :param user_id:
    :param workout_data:
    :return:
    """
    return Workout.objects.create(user=user_id, **workout_data)


@database_sync_to_async
def create_workout_filter(telegram_user, workout_data):
    """
    Проверяем, существует ли уже тренировка с таким же названием для данного пользователя
    :param telegram_user:
    :param workout_data:
    :return:
    """
    workout_name = workout_data.get('name')    #Извлекаем название тренировки из переданных данных
    return Workout.objects.filter(user=telegram_user, name=workout_name).first()



@database_sync_to_async
def get_user_workout(user_id, name):
    """
    Получение тренировки пользователя по названию
    :param user_id:
    :return:
    """
    return Workout.objects.get(user=user_id, name=name)


@database_sync_to_async
def get_user_workout_exercises(user_id, workout):
    """
    Получение упражнений с определенной тренировки
    :param user_id:
    :return:
    """
    return list(Exercise.objects.filter(user=user_id, workout=workout))


@database_sync_to_async
def create_exercise(user_id, exersize_data):
    """
    Создание нового объекта Упражнения
    :param user_id:
    :param workout_data:
    :return:
    """
    return Exercise.objects.create(user=user_id, **exersize_data)


@database_sync_to_async
def create_exercise_filter(telegram_user, exercise_data):
    """Проверяем, существует ли уже упражнение с таким же названием для данного пользователя
    :param telegram_user:
    :param exercise_data:
    :return:
    """
    exercise_name = exercise_data.get('name')    #Извлекаем название упражнения из переданных данных
    exercise_workout = exercise_data.get('workout')
    return Exercise.objects.filter(user=telegram_user, name=exercise_name, workout=exercise_workout).first()


@database_sync_to_async
def get_user_exercise(user_id, name, workout):
    """
    Получение тренировки пользователя по названию
    :param user_id:
    :return:
    """
    return Exercise.objects.get(user=user_id, name=name, workout=workout)


@database_sync_to_async
def create_set(user_id, set_data):
    """
    Создание нового объекта Сета
    :param user_id:
    :param workout_data:
    :return:
    """
    return Sets.objects.create(**set_data)


@database_sync_to_async
def get_user_exercise_sets(user_id, selected_exercise):
    """
    Получение cетов упражнения с определенной тренировки
    :param user_id:
    :return:
    """
    return list(Sets.objects.filter(exercise__user=user_id, exercise=selected_exercise))

