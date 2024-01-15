from django.db import models


# Create your models here.
class TelegramUser(models.Model):
    """
    Класс Пользователь для связи с айди из телеграма
    """
    telegram_id = models.BigIntegerField(unique=True, verbose_name="ID пользователя в Telegram")

    def __str__(self):
        return str(self.telegram_id)

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"


class Workout(models.Model):
    """
    Класс Тренировка
    """
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name="Название тренировки")
    #exercises = models.ManyToManyField(Exercise, blank=True, related_name='Упражнения')
    date = models.DateField(auto_now_add=True, verbose_name="Дата создания")


    def __str__(self):
        return f"{self.name} ({self.date})"

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"


class Exercise(models.Model):
    """
    Класс Упражнение
    """
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=255, verbose_name="Название упражнения")
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, null=True, verbose_name='Тренировка')

    def __str__(self):
        return f'{self.name} - {self.workout}'

    class Meta:
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"


class Sets(models.Model):
    """
    Класс сеты упражнения
    """
    set = models.PositiveIntegerField(default=1, verbose_name="Подход")
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Вес")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата выполнения")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, null=True, verbose_name="Упражнение")

    def __str__(self):
        return f'{self.set} - {self.weight}, {self.exercise}'

    class Meta:
        verbose_name = "Сет"
        verbose_name_plural = "Сеты"



