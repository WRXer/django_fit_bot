from django.contrib import admin
from .models import Exercise, Workout, Sets


# Register your models here.
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    pass

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    pass

@admin.register(Sets)
class SetsAdmin(admin.ModelAdmin):
    pass