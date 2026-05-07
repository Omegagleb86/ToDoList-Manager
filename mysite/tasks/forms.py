from django import forms

from .models import TodoList


class TodoListForm(forms.ModelForm):
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
