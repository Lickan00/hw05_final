from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CreationForm


class SignUp(CreateView):
    """Передаем в шаблон форму с полями из CreationForm"""
    """После заполнения формы переадресация на name='posts:index"""
    """Данные, отправленные через форму, будут переданы в модель User"""
    """и сохранены в БД"""
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
