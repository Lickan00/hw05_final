from django.db import models
from django.contrib.auth import get_user_model

from posts.constants import TEXT_BACK_LIMIT

User = get_user_model()


class Group(models.Model):
    """Класс для генерации group/"""
    title = models.CharField(max_length=200, verbose_name='Title in group')
    slug = models.SlugField(unique=True, verbose_name='Slug in group')
    description = models.TextField(verbose_name='Description group')

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    """Класс для генерации постов"""
    text = models.TextField(
        verbose_name='text',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='pub_date'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='author',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='group',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:TEXT_BACK_LIMIT]


class Comment(models.Model):
    """Класс для генерации комментариев"""
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='author',
    )
    text = models.TextField(
        verbose_name='text',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='created_date'
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    """Класс для подписок на авторов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )
