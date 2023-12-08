from django.contrib import admin
from .models import Exercise, Workout



# Register your models here.
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    pass

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    pass