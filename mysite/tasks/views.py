from collections import OrderedDict

from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views import View

from .models import Task, TodoList, TodoUser


def get_demo_user():
    return TodoUser.objects.order_by('id').first()


class DashboardView(View):
    template_name = 'tasks/dashboard.html'

    def get(self, request):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            return render(request, self.template_name, {'user_obj': None})

        todo_lists = (
            TodoList.objects.filter(user=user, is_archived=False)
            .annotate(task_count=Count('tasks'))
            .order_by('position', 'title')
        )
        recent_tasks = (
            Task.objects.filter(user=user, is_deleted=False)
            .select_related('todo_list')
            .order_by('-updated_at')[:8]
        )
        context = {
            'user_obj': user,
            'todo_lists': todo_lists,
            'recent_tasks': recent_tasks,
            'stats': {
                'lists': todo_lists.count(),
                'tasks': Task.objects.filter(user=user, is_deleted=False).count(),
                'in_progress': Task.objects.filter(
                    user=user,
                    status=Task.Status.IN_PROGRESS,
                    is_deleted=False,
                ).count(),
                'done': Task.objects.filter(
                    user=user,
                    status=Task.Status.DONE,
                    is_deleted=False,
                ).count(),
            },
        }
        return render(request, self.template_name, context)


class TodoListDetailView(View):
    template_name = 'tasks/list_detail.html'

    def get(self, request, pk):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            raise Http404('Нет пользователя для демонстрации.')

        todo_list = TodoList.objects.filter(user=user, pk=pk).first()
        if todo_list is None:
            raise Http404('Список задач не найден.')

        tasks = (
            Task.objects.filter(todo_list=todo_list, user=user, is_deleted=False)
            .order_by('status', 'position', '-created_at')
        )
        columns = OrderedDict(
            (status, {'label': label, 'tasks': []}) for status, label in Task.Status.choices
        )
        priority_matrix = OrderedDict(
            [
                ('important_urgent', {'label': 'Важно и срочно', 'tasks': []}),
                ('important_not_urgent', {'label': 'Важно, не срочно', 'tasks': []}),
                ('not_important_urgent', {'label': 'Срочно, не важно', 'tasks': []}),
                ('not_important_not_urgent', {'label': 'Не срочно и не важно', 'tasks': []}),
            ]
        )

        for task in tasks:
            columns[task.status]['tasks'].append(task)
            if task.is_important and task.is_urgent:
                priority_matrix['important_urgent']['tasks'].append(task)
            elif task.is_important:
                priority_matrix['important_not_urgent']['tasks'].append(task)
            elif task.is_urgent:
                priority_matrix['not_important_urgent']['tasks'].append(task)
            else:
                priority_matrix['not_important_not_urgent']['tasks'].append(task)

        return render(
            request,
            self.template_name,
            {
                'user_obj': user,
                'todo_list': todo_list,
                'columns': columns,
                'priority_matrix': priority_matrix,
            },
        )


class DemoApiView(View):
    def get(self, request):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            return JsonResponse({'detail': 'No demo data yet. Run seed_demo.'}, status=404)

        lists_payload = []
        for todo_list in TodoList.objects.filter(user=user).order_by('position', 'title'):
            tasks = Task.objects.filter(
                user=user,
                todo_list=todo_list,
                is_deleted=False,
            ).order_by('status', 'position')
            lists_payload.append(
                {
                    'id': todo_list.id,
                    'title': todo_list.title,
                    'archived': todo_list.is_archived,
                    'tasks': [
                        {
                            'id': task.id,
                            'title': task.title,
                            'status': task.status,
                            'priority': task.priority_label,
                            'position': task.position,
                        }
                        for task in tasks
                    ],
                }
            )

        return JsonResponse(
            {
                'user': user.username,
                'list_count': len(lists_payload),
                'lists': lists_payload,
            },
            json_dumps_params={'ensure_ascii': False, 'indent': 2},
        )
