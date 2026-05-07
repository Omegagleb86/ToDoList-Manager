from django import forms

from .models import TodoList


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
