from django import forms

from .models import Task, TodoList


class TodoListForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_title(self):
        title = self.cleaned_data['title']
        if self.user and TodoList.objects.filter(user=self.user, title=title).exists():
            raise forms.ValidationError('У пользователя уже есть список с таким названием.')
        return title

    def save(self, commit=True):
        todo_list = super().save(commit=False)
        if self.user is not None:
            todo_list.user = self.user
        if commit:
            todo_list.save()
        return todo_list

    class Meta:
        model = TodoList
        fields = ('title', 'description', 'color', 'icon')
        labels = {
            'title': 'Название списка',
            'description': 'Описание',
            'color': 'Цвет',
            'icon': 'Иконка',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Например: Учебная практика',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Кратко опиши, для чего нужен этот список',
                    'rows': 4,
                }
            ),
            'color': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '#2563eb',
                    'type': 'color',
                }
            ),
            'icon': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Например: book-open',
                }
            ),
        }
        help_texts = {
            'color': 'Выбери цвет списка или оставь поле без изменений.',
            'icon': 'Название иконки можно будет использовать в интерфейсе позже.',
        }


class TaskForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        required=False,
        label='Дата старта',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            },
        ),
    )
    due_date = forms.DateTimeField(
        required=False,
        label='Дедлайн',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            },
        ),
    )

    def __init__(self, *args, user=None, todo_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.todo_list = todo_list

    def save(self, commit=True):
        task = super().save(commit=False)
        if self.user is not None:
            task.user = self.user
        if self.todo_list is not None:
            task.todo_list = self.todo_list
        if commit:
            task.save()
        return task

    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'status',
            'is_important',
            'is_urgent',
            'start_date',
            'due_date',
        )
        labels = {
            'title': 'Название задачи',
            'description': 'Описание',
            'status': 'Статус',
            'is_important': 'Важная',
            'is_urgent': 'Срочная',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Например: Подготовить отчет',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Добавь детали задачи',
                    'rows': 4,
                }
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_important': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
