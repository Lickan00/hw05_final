import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import User, Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='DimaB')
        cls.group_1 = Group.objects.create(
            title='tests_group',
            slug='tests_group',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Проверка создания поста c редиректорм в профиль юзера"""
        post_count = Post.objects.count()
        before_create = set(Post.objects.all())
        form_data = {
            'group': PostCreateFormTests.group_1.pk,
            'text': 'Тестовый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostCreateFormTests.user}
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)
        after_create = set(Post.objects.all())
        self.assertEqual(len(after_create - before_create), 1)
        objects_after_create = after_create.pop()
        self.assertEqual(objects_after_create.text, form_data['text'])
        self.assertEqual(objects_after_create.group.pk, form_data['group'])
        self.assertEqual(objects_after_create.author, self.user)

    def test_edit_post(self):
        """Проверка изменения поста"""
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый текст',
        )
        form_data = {
            'group': PostCreateFormTests.group_1.pk,
            'text': 'Тестовый текст отредактирован',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        error_name_one = 'Данные поста не совпадают'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        author=PostCreateFormTests.user,
                        group=form_data['group'],
                        id=post.pk
                        ), error_name_one)

    def test_create_comment_authorized_user(self):
        """Создание комментария и проверка редиректа"""
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый текст',
        )
        before_create = set(Comment.objects.all())
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        after_create = set(Comment.objects.all())
        self.assertEqual(len(after_create - before_create), 1)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.pk}
        ))
        objects_after_create = after_create.pop()
        self.assertEqual(objects_after_create.text, form_data['text'])
        self.assertEqual(objects_after_create.author, self.user)

    def test_create_comment_guest_user(self):
        """"Проверяем что комментарий не создастся, без авторизации"""
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый текст',
        )
        form_data = {
            'text': 'Тестовый комментарий'
        }
        before_create = set(Comment.objects.all())
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        after_create = set(Comment.objects.all())
        self.assertEqual(len(after_create - before_create), 0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_with_a_picture(self):
        """Проверка создания поста c картинкой + редирект"""
        post_count = Post.objects.count()
        before_create = set(Post.objects.all())
        image_bytes_literals = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.jpeg',
            content=image_bytes_literals,
            content_type='image/jpeg'
        )
        form_data = {
            'group': PostCreateFormTests.group_1.pk,
            'text': 'Тестовый текст с картинкой',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostCreateFormTests.user}
        ))
        after_create = set(Post.objects.all())
        self.assertEqual(len(after_create - before_create), 1)
        objects_after_create = after_create.pop()
        self.assertEqual(objects_after_create.text, form_data['text'])
        self.assertEqual(objects_after_create.group.pk, form_data['group'])
        self.assertEqual(
            objects_after_create.image,
            f'posts/{form_data["image"].name}'
        )
