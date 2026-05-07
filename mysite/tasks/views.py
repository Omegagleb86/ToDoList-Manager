from collections import OrderedDict

from django.contrib import messages
from django.db.models import Count, Max
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from .forms import TaskForm, TodoListForm
from .models import Task, TodoList, TodoUser


def get_demo_user():
    return TodoUser.objects.order_by('id').first()


class DashboardView(View):
    template_name = 'tasks/dashboard.html'

    def get(self, request):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            return render(
                request,
                self.template_name,
                {
                    'user_obj': None,
                    'todo_list_form': TodoListForm(),
                    'is_create_list_form_open': False,
                },
            )

        return render(
            request,
            self.template_name,
            self.get_context(user, todo_list_form=TodoListForm(user=user)),
        )

    def post(self, request):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            messages.error(request, 'Нельзя создать список: пользователь не найден.')
            return redirect('tasks:dashboard')

        form = TodoListForm(request.POST, user=user)
        if form.is_valid():
            todo_list = form.save(commit=False)
            max_position = TodoList.objects.filter(user=user).aggregate(Max('position'))[
                'position__max'
            ]
            todo_list.position = 0 if max_position is None else max_position + 1
            todo_list.save()
            messages.success(request, 'Список задач создан.')
            return redirect('tasks:dashboard')

        return render(
            request,
            self.template_name,
            self.get_context(
                user,
                todo_list_form=form,
                is_create_list_form_open=True,
            ),
        )

    def get_context(self, user, todo_list_form, is_create_list_form_open=False):
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
            'todo_list_form': todo_list_form,
            'is_create_list_form_open': is_create_list_form_open,
        }
        return context


class TodoListDetailView(View):
    template_name = 'tasks/list_detail.html'

    def get(self, request, pk):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            raise Http404('Нет пользователя для демонстрации.')

        todo_list = TodoList.objects.filter(user=user, pk=pk).first()
        if todo_list is None:
            raise Http404('Список задач не найден.')

        return render(
            request,
            self.template_name,
            self.get_context(
                user,
                todo_list,
                task_form=TaskForm(user=user, todo_list=todo_list),
            ),
        )

    def post(self, request, pk):
        user = request.user if request.user.is_authenticated else get_demo_user()
        if user is None:
            raise Http404('Нет пользователя для демонстрации.')

        todo_list = TodoList.objects.filter(user=user, pk=pk).first()
        if todo_list is None:
            raise Http404('Список задач не найден.')

        form = TaskForm(request.POST, user=user, todo_list=todo_list)
        if form.is_valid():
            task = form.save(commit=False)
            max_position = Task.objects.filter(
                todo_list=todo_list,
                status=task.status,
                is_deleted=False,
            ).aggregate(Max('position'))['position__max']
            task.position = 0 if max_position is None else max_position + 1
            task.save()
            messages.success(request, 'Задача создана.')
            return redirect('tasks:list_detail', pk=todo_list.pk)

        return render(
            request,
            self.template_name,
            self.get_context(
                user,
                todo_list,
                task_form=form,
                is_create_task_form_open=True,
            ),
        )

    def get_context(self, user, todo_list, task_form, is_create_task_form_open=False):
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

        return {
            'user_obj': user,
            'todo_list': todo_list,
            'columns': columns,
            'priority_matrix': priority_matrix,
            'task_form': task_form,
            'is_create_task_form_open': is_create_task_form_open,
        }


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
