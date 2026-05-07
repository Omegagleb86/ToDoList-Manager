from collections import OrderedDict

from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Count, Max
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from .forms import TaskForm, TodoAuthenticationForm, TodoListForm, TodoUserCreationForm
from .models import Task, TodoList, TodoUser


class AuthView(View):
    template_name = 'tasks/auth.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('tasks:dashboard')
        return render(
            request,
            self.template_name,
            {
                'login_form': TodoAuthenticationForm(request=request),
                'register_form': TodoUserCreationForm(),
            },
        )

    def post(self, request):
        action = request.POST.get('form_action')
        if action == 'register':
            register_form = TodoUserCreationForm(request.POST)
            login_form = TodoAuthenticationForm(request=request)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                messages.success(request, 'Аккаунт создан. Добро пожаловать.')
                return redirect('tasks:dashboard')
        else:
            login_form = TodoAuthenticationForm(request=request, data=request.POST)
            register_form = TodoUserCreationForm()
            if login_form.is_valid():
                login(request, login_form.get_user())
                messages.success(request, 'Ты вошел в аккаунт.')
                return redirect('tasks:dashboard')

        return render(
            request,
            self.template_name,
            {
                'login_form': login_form,
                'register_form': register_form,
                'active_form': 'register' if action == 'register' else 'login',
            },
        )


class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.success(request, 'Ты вышел из аккаунта.')
        return redirect('tasks:auth')


class DashboardView(View):
    template_name = 'tasks/dashboard.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('tasks:auth')

        return render(
            request,
            self.template_name,
            self.get_context(request.user, todo_list_form=TodoListForm(user=request.user)),
        )

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('tasks:auth')

        user = request.user

        action = request.POST.get('form_action')
        if action == 'edit_list':
            return self.update_list(request, user)
        if action == 'delete_list':
            return self.delete_list(request, user)

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
                edit_todo_list_form=TodoListForm(user=user, prefix='edit_list'),
                is_create_list_form_open=True,
            ),
        )

    def update_list(self, request, user):
        todo_list = TodoList.objects.filter(user=user, pk=request.POST.get('list_id')).first()
        if todo_list is None:
            raise Http404('Список задач не найден.')

        form = TodoListForm(
            request.POST,
            instance=todo_list,
            user=user,
            prefix='edit_list',
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Список задач обновлен.')
            return redirect('tasks:dashboard')

        return render(
            request,
            self.template_name,
            self.get_context(
                user,
                todo_list_form=TodoListForm(user=user),
                edit_todo_list_form=form,
                edit_todo_list_id=todo_list.pk,
                is_edit_list_form_open=True,
            ),
        )

    def delete_list(self, request, user):
        todo_list = TodoList.objects.filter(user=user, pk=request.POST.get('list_id')).first()
        if todo_list is None:
            raise Http404('Список задач не найден.')

        todo_list.delete()
        messages.success(request, 'Список задач удален.')
        return redirect('tasks:dashboard')

    def get_context(
        self,
        user,
        todo_list_form,
        edit_todo_list_form=None,
        is_create_list_form_open=False,
        is_edit_list_form_open=False,
        edit_todo_list_id=None,
    ):
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
            'edit_todo_list_form': edit_todo_list_form
            or TodoListForm(user=user, prefix='edit_list'),
            'is_create_list_form_open': is_create_list_form_open,
            'is_edit_list_form_open': is_edit_list_form_open,
            'edit_todo_list_id': edit_todo_list_id,
        }
        return context


class TodoListDetailView(View):
    template_name = 'tasks/list_detail.html'

    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('tasks:auth')

        user = request.user
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
                edit_task_form=TaskForm(user=user, todo_list=todo_list, prefix='edit'),
            ),
        )

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('tasks:auth')

        user = request.user
        todo_list = TodoList.objects.filter(user=user, pk=pk).first()
        if todo_list is None:
            raise Http404('Список задач не найден.')

        if request.POST.get('form_action') == 'edit_task':
            return self.update_task(request, user, todo_list)
        if request.POST.get('form_action') == 'delete_task':
            return self.delete_task(request, user, todo_list)

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
                edit_task_form=TaskForm(user=user, todo_list=todo_list, prefix='edit'),
                is_create_task_form_open=True,
            ),
        )

    def update_task(self, request, user, todo_list):
        task = Task.objects.filter(
            user=user,
            todo_list=todo_list,
            pk=request.POST.get('task_id'),
            is_deleted=False,
        ).first()
        if task is None:
            raise Http404('Задача не найдена.')

        previous_status = task.status
        form = TaskForm(
            request.POST,
            instance=task,
            user=user,
            todo_list=todo_list,
            prefix='edit',
        )
        if form.is_valid():
            updated_task = form.save(commit=False)
            if updated_task.status != previous_status:
                max_position = Task.objects.filter(
                    todo_list=todo_list,
                    status=updated_task.status,
                    is_deleted=False,
                ).exclude(pk=updated_task.pk).aggregate(Max('position'))['position__max']
                updated_task.position = 0 if max_position is None else max_position + 1
            updated_task.save()
            messages.success(request, 'Задача обновлена.')
            return redirect('tasks:list_detail', pk=todo_list.pk)

        return render(
            request,
            self.template_name,
            self.get_context(
                user,
                todo_list,
                task_form=TaskForm(user=user, todo_list=todo_list),
                edit_task_form=form,
                edit_task_id=task.pk,
                is_edit_task_form_open=True,
            ),
        )

    def delete_task(self, request, user, todo_list):
        task = Task.objects.filter(
            user=user,
            todo_list=todo_list,
            pk=request.POST.get('task_id'),
            is_deleted=False,
        ).first()
        if task is None:
            raise Http404('Задача не найдена.')

        task.is_deleted = True
        task.save()
        messages.success(request, 'Задача удалена.')
        return redirect('tasks:list_detail', pk=todo_list.pk)

    def get_context(
        self,
        user,
        todo_list,
        task_form,
        edit_task_form,
        is_create_task_form_open=False,
        is_edit_task_form_open=False,
        edit_task_id=None,
    ):
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
            'edit_task_form': edit_task_form,
            'is_create_task_form_open': is_create_task_form_open,
            'is_edit_task_form_open': is_edit_task_form_open,
            'edit_task_id': edit_task_id,
        }


class DemoApiView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Authentication required.'}, status=403)

        user = request.user

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
