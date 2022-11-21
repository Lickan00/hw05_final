from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Класс для формы создания поста"""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': "Текст поста",
            'group': "Группа",
            'image': "Изображение",
        }
        help_texts = {
            'text': "Текст нового поста",
            'group': "Группа, к которой будет относиться пост",
            'image': "Изображение к посту",
        }


class CommentForm(forms.ModelForm):
    """Класс для формы создания поста"""
    class Meta:
        model = Comment
        fields = (
            'text',
        )
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
