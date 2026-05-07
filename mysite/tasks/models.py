from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class TodoUser(AbstractUser):
    timezone = models.CharField(max_length=64, default='Asia/Yekaterinburg')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class TodoList(models.Model):
    user = models.ForeignKey(
        TodoUser,
        on_delete=models.CASCADE,
        related_name='todo_lists',
        verbose_name='Пользователь',
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    color = models.CharField(max_length=7, blank=True, verbose_name='Цвет')
    position = models.PositiveIntegerField(default=0, verbose_name='Позиция')
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name = 'Список задач'
        verbose_name_plural = 'Списки задач'
        ordering = ['position', 'title']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'title'],
                name='unique_todo_list_title_per_user',
            ),
        ]
        indexes = [
            models.Index(fields=['user'], name='todo_list_user_idx'),
            models.Index(fields=['user', 'is_archived'], name='todo_list_user_arch_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.user})'


class Task(models.Model):
    class Status(models.TextChoices):
        QUEUE = 'queue', 'Очередь'
        IN_PROGRESS = 'in_progress', 'В работе'
        DONE = 'done', 'Выполнено'
        ARCHIVED = 'archived', 'Архивировано'

    user = models.ForeignKey(
        TodoUser,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Пользователь',
    )
    todo_list = models.ForeignKey(
        TodoList,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Список задач',
    )
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')
    color = models.CharField(max_length=7, blank=True, verbose_name='Цвет')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUE,
        verbose_name='Статус',
    )
    position = models.PositiveIntegerField(default=0, verbose_name='Позиция')
    is_important = models.BooleanField(default=False, verbose_name='Важно')
    is_urgent = models.BooleanField(default=False, verbose_name='Срочно')
    start_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата старта')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершена')
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name='Архивирована')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалена')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Удалена в')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['todo_list__position', 'status', 'position', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['todo_list', 'status', 'position'],
                condition=Q(is_deleted=False),
                name='unique_task_position_per_status',
            ),
            models.CheckConstraint(
                check=Q(position__gte=0),
                name='task_position_gte_0',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'status'], name='task_user_status_idx'),
            models.Index(fields=['todo_list', 'status'], name='task_list_status_idx'),
            models.Index(
                fields=['user', 'is_important', 'is_urgent'],
                name='task_priority_matrix_idx',
            ),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def priority_label(self) -> str:
        if self.is_important and self.is_urgent:
            return 'Важно и срочно'
        if self.is_important:
            return 'Важно, не срочно'
        if self.is_urgent:
            return 'Срочно, не важно'
        return 'Без высокого приоритета'

    def clean(self) -> None:
        if self.todo_list_id and self.user_id and self.todo_list.user_id != self.user_id:
            raise ValidationError('Пользователь задачи должен совпадать с владельцем списка.')
        if self.completed_at and self.created_at and self.completed_at < self.created_at:
            raise ValidationError('Дата завершения не может быть раньше даты создания.')
        if self.due_date and self.start_date and self.due_date < self.start_date:
            raise ValidationError('Дедлайн не может быть раньше даты старта.')

    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.status == self.Status.DONE and self.completed_at is None:
            self.completed_at = now
        if self.status != self.Status.DONE:
            self.completed_at = None
        if self.status == self.Status.ARCHIVED and self.archived_at is None:
            self.archived_at = now
        if self.status != self.Status.ARCHIVED:
            self.archived_at = None
        if self.is_deleted and self.deleted_at is None:
            self.deleted_at = now
        if not self.is_deleted:
            self.deleted_at = None
        self.full_clean()
        super().save(*args, **kwargs)
