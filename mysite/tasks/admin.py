from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Task, TodoList, TodoUser


@admin.register(TodoUser)
class TodoUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Настройки приложения', {'fields': ('timezone',)}),
    )
    list_display = ('username', 'email', 'is_staff', 'is_active', 'timezone')
    search_fields = ('username', 'email')


@admin.register(TodoList)
class TodoListAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'position', 'is_archived', 'updated_at')
    list_filter = ('is_archived', 'user')
    search_fields = ('title', 'description', 'user__username')
    ordering = ('user', 'position', 'title')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'todo_list',
        'status',
        'position',
        'is_important',
        'is_urgent',
        'due_date',
        'is_deleted',
    )
    list_filter = ('status', 'is_important', 'is_urgent', 'is_deleted', 'todo_list')
    search_fields = ('title', 'description', 'user__username', 'todo_list__title')
    ordering = ('todo_list', 'status', 'position')
