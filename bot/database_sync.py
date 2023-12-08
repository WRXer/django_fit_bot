from channels.db import database_sync_to_async
from workout.models import Workout, TelegramUser


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
