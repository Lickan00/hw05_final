import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Post, Group, Comment, Follow
from ..constants import POSTS_PER_PAGE, POSTS_FOR_BULK_CREATE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.group = Group.objects.create(
            title='tests_group',
            slug='tests_group',
        )
        cls.group_2 = Group.objects.create(
            title='tests_group_2',
            slug='tests_group_2',
        )
        cls.user = User.objects.create_user(username='DimaB')
        cls.user_2 = User.objects.create_user(username='Yuliya')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.user,
            text='Тестовый комментарий',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(self.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)
        self.assertEqual(first_object.pk, self.post.pk)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.id, self.group.pk)
        self.assertEqual(first_object.pub_date, self.post.pub_date)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        second_object = response.context['group']
        self.assertEqual(first_object.pk, self.post.pk)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.id, self.group.pk)
        self.assertEqual(first_object.author.username, self.user.username)
        self.assertEqual(second_object.id, self.group.pk)
        self.assertEqual(second_object.title, self.group.title)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['posts'][0]
        second_object = response.context['author']
        self.assertEqual(first_object.pk, self.post.pk)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.id, self.group.pk)
        self.assertEqual(first_object.author.username, self.user.username)
        self.assertEqual(second_object, self.user)
        self.assertEqual(second_object.id, self.user.pk)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post_object = response.context['post']
        self.assertEqual(post_object, self.post)
        self.assertEqual(post_object.pk, self.post.pk)
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.pub_date, self.post.pub_date)
        self.assertEqual(
            post_object.author.username, self.user.username
        )
        comments_object = response.context['comments'][0]
        self.assertEqual(comments_object.pk, self.comment.pk)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                post_object = response.context['post']
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEquals(post_object.author, self.user)
                self.assertEquals(post_object.pk, self.post.pk)
                self.assertEquals(post_object.text, self.post.text)
                self.assertEquals(post_object.group, self.post.group)

    def test_post_create_displayed_on_expected_pages(self):
        """Если при создании поста указать группу, то этот пост появляется"""
        cache.clear()
        new_post = Post.objects.create(
            author=self.user,
            text='Тестовый текст №2',
            group=self.group,
        )
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            reverse('posts:profile', kwargs={'username': self.user}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse('posts:index'))
                cache.clear()
                first_object = response.context['page_obj'][0]
                error_assert = f'Поста нет в {url}'
                self.assertEqual(first_object, new_post, error_assert)

    def test_post_added_correctly_group(self):
        """"Проверка что пост не попал в группу,
        для которой не был предназначен"""
        posts_count = Post.objects.filter(group=self.group_2).count()
        self.assertEqual(posts_count, 0, 'пост найден в другой группе')

    def test_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок"""
        error_one = 'В БД найден объект которого не должно быть'
        self.assertFalse(Follow.objects.filter(
            user=self.user_2, author=self.user
        ), error_one)
        self.authorized_client_two.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}
        ))
        error_two = 'В БД не найден ожидаемый объект'
        self.assertTrue(Follow.objects.filter(
            user=self.user_2, author=self.user
        ), error_two)
        self.authorized_client_two.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user.username}
        ))
        error_three = 'Из БД не был удален ожидаемый объект'
        self.assertFalse(Follow.objects.filter(
            user=self.user_2, author=self.user
        ), error_three)

    def test_follow_displayed_on_expected_pages(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан"""
        self.authorized_client_two.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}
        ))
        new_post = Post.objects.create(
            author=self.user,
            text='Тестовый текст №2',
            group=self.group,
        )
        response_user_two = self.authorized_client_two.get(
            reverse('posts:follow_index')
        )
        first_object = response_user_two.context['page_obj'][0]
        error = f'Нового поста нет на странице follow у {self.user_2}'
        self.assertEqual(first_object.pk, new_post.pk, error)
        self.assertEqual(len(response_user_two.context['page_obj']), 2)
        response_user_one = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        self.assertEqual(len(response_user_one.context['page_obj']), 0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_show_correct_context_with_a_picture(self):
        """При выводе страницы с картинкой,
        изображение передаётся в словаре context"""
        cache.clear()
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
        post_two = Post.objects.create(
            author=ViewsTest.user,
            text='Текст c картинкой',
            group=ViewsTest.group,
            image=uploaded
        )
        reverse_objects = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': post_two.group.slug}),
            reverse('posts:profile', kwargs={'username': post_two.author})
        )
        for reverse_object in reverse_objects:
            with self.subTest(reverse=reverse):
                response = self.client.get(reverse_object)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.pk, post_two.pk)
                self.assertEqual(first_object.text, post_two.text)
                self.assertEqual(first_object.image, post_two.image)
        response_post_detail = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_two.pk})
        )
        first_object = response_post_detail.context['post']
        self.assertEqual(first_object.pk, post_two.pk)
        self.assertEqual(first_object.image, post_two.image)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='tests_group',
            slug='tests_group',
        )
        cls.user = User.objects.create_user(username='UserBDV')
        posts_list = []
        for i in range(POSTS_FOR_BULK_CREATE):
            posts_list.append(Post(
                author=cls.user,
                text=f'Текстовый текст {i}',
                group=cls.group,
            ))
        cls.post = Post.objects.bulk_create(posts_list)

    def test_pages_contains_thirteen_records(self):
        """Тестируем паджинатор"""
        cache.clear()
        test_pages = (
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ),
        )
        for page in test_pages:
            with self.subTest(page=page):
                first_page_response = self.client.get(page)
                second_page_response = self.client.get(page + '?page=2')
                error_response = f'Страница {page}, не прошла тест'
                self.assertEqual(
                    len(first_page_response.context['page_obj']),
                    POSTS_PER_PAGE,
                    error_response
                )
                self.assertEqual(
                    len(second_page_response.context['page_obj']),
                    (POSTS_FOR_BULK_CREATE - POSTS_PER_PAGE),
                    error_response
                )


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='DimaB')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестируем кэш',
        )

    def test_cache_index_page(self):
        """Тестируем cache главной страницы"""
        response = self.client.get(reverse('posts:index'))
        before_delete = response.content
        Post.objects.all().delete()
        after_delete = response.content
        self.assertEqual(after_delete, before_delete)
        cache.clear()
        after_clear_cache = self.client.get(reverse('posts:index'))
        self.assertIsNot(after_clear_cache.content, after_delete)
