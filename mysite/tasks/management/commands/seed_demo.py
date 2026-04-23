from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Task, TodoList, TodoUser


class Command(BaseCommand):
    help = 'Создает демо-пользователя, списки и задачи для показа проекта.'

    def handle(self, *args, **options):
        user, created = TodoUser.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'timezone': 'Asia/Yekaterinburg',
            },
        )
        if created:
            user.set_password('demo12345')
            user.save()

        admin_user, admin_created = TodoUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
                'timezone': 'Asia/Yekaterinburg',
            },
        )
        if admin_created:
            admin_user.set_password('admin12345')
            admin_user.save()

        now = timezone.now()
        lists_spec = [
            ('Учеба в университете', 'Лабораторные, дедлайны и подготовка к парам', '#2563eb', 'school'),
            ('Работа', 'Рабочие задачи и договоренности', '#059669', 'briefcase'),
            ('Домашние дела', 'Бытовые и личные активности', '#ea580c', 'home'),
        ]

        created_lists = []
        for idx, (title, description, color, icon) in enumerate(lists_spec):
            todo_list, _ = TodoList.objects.get_or_create(
                user=user,
                title=title,
                defaults={
                    'description': description,
                    'color': color,
                    'icon': icon,
                    'position': idx,
                },
            )
            created_lists.append(todo_list)

        tasks_spec = [
            (
                created_lists[0],
                'Подготовить отчет по Django',
                Task.Status.IN_PROGRESS,
                0,
                True,
                True,
                now + timedelta(days=1),
            ),
            (
                created_lists[0],
                'Сделать лабораторную по Java',
                Task.Status.QUEUE,
                0,
                True,
                False,
                now + timedelta(days=4),
            ),
            (
                created_lists[1],
                'Созвон с заказчиком',
                Task.Status.DONE,
                0,
                True,
                True,
                now - timedelta(hours=3),
            ),
            (
                created_lists[1],
                'Разобрать почту',
                Task.Status.QUEUE,
                1,
                False,
                True,
                now + timedelta(days=2),
            ),
            (
                created_lists[2],
                'Купить продукты',
                Task.Status.IN_PROGRESS,
                1,
                False,
                True,
                now + timedelta(hours=10),
            ),
            (
                created_lists[2],
                'Разобрать шкаф',
                Task.Status.ARCHIVED,
                0,
                False,
                False,
                None,
            ),
        ]

        for todo_list, title, status, position, important, urgent, due_date in tasks_spec:
            Task.objects.get_or_create(
                user=user,
                todo_list=todo_list,
                title=title,
                defaults={
                    'description': f'Демо-задача для списка "{todo_list.title}".',
                    'status': status,
                    'position': position,
                    'is_important': important,
                    'is_urgent': urgent,
                    'due_date': due_date,
                    'start_date': now - timedelta(days=1),
                },
            )

        self.stdout.write(self.style.SUCCESS('Демо-данные готовы.'))
        self.stdout.write('Пользователь demo / demo12345')
        self.stdout.write('Админ admin / admin12345')
