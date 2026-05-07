from django import forms

from .models import Task, TodoList


FORM_CONTROL_CLASS = (
    'w-full rounded-lg border border-[#6f5a5a] bg-[#2a2020] px-3 py-2 text-sm '
    'text-[#f4eeee] placeholder:text-[#a99797] shadow-sm '
    'focus:border-[#7fc8ff] focus:outline-none focus:ring-1 focus:ring-[#7fc8ff]'
)
CHECKBOX_CLASS = (
    'h-4 w-4 rounded border-[#6f5a5a] bg-[#2a2020] text-[#7fc8ff] '
    'focus:ring-[#7fc8ff] focus:ring-offset-[#3b2d2d]'
)


class TodoListForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_title(self):
        title = self.cleaned_data['title']
        lists = TodoList.objects.filter(user=self.user, title=title)
        if self.instance.pk:
            lists = lists.exclude(pk=self.instance.pk)
        if self.user and lists.exists():
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
                    'class': FORM_CONTROL_CLASS,
                    'placeholder': 'Например: Учебная практика',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': FORM_CONTROL_CLASS,
                    'placeholder': 'Кратко опиши, для чего нужен этот список',
                    'rows': 4,
                }
            ),
            'color': forms.TextInput(
                attrs={
                    'class': FORM_CONTROL_CLASS + ' h-11 p-1',
                    'placeholder': '#2563eb',
                    'type': 'color',
                }
            ),
            'icon': forms.TextInput(
                attrs={
                    'class': FORM_CONTROL_CLASS,
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
                'class': FORM_CONTROL_CLASS,
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
                'class': FORM_CONTROL_CLASS,
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
                    'class': FORM_CONTROL_CLASS,
                    'placeholder': 'Например: Подготовить отчет',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': FORM_CONTROL_CLASS,
                    'placeholder': 'Добавь детали задачи',
                    'rows': 4,
                }
            ),
            'status': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
            'is_important': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'is_urgent': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }
