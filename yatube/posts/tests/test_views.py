import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Post, Group, Comment, Follow
from ..constants import POSTS_PER_PAGE, POSTS_FOR_BULK_CREATE
from ..forms import CommentForm, PostForm

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
        cls.image_bytes_literals = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.jpeg',
            content=cls.image_bytes_literals,
            content_type='image/jpeg'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def assert_method_for_tests_first_object(self, first_object):
        """Проверки для first_object"""
        self.assertEqual(first_object, self.post)
        self.assertEqual(first_object.pk, self.post.pk)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.id, self.group.pk)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(first_object.author.username, self.user.username)

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
        self.assert_method_for_tests_first_object(first_object)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        self.assert_method_for_tests_first_object(first_object)
        second_object = response.context['group']
        self.assertEqual(second_object.id, self.group.pk)
        self.assertEqual(second_object.title, self.group.title)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['posts'][0]
        self.assert_method_for_tests_first_object(first_object)
        author_object = response.context['author']
        self.assertEqual(author_object, self.user)
        self.assertEqual(author_object.id, self.user.pk)
        following_object = response.context['following']
        self.assertFalse(following_object)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        first_object = response.context['post']
        self.assert_method_for_tests_first_object(first_object)
        self.assertIsInstance(response.context.get('form'), CommentForm)
        comments_object = response.context['comments'][0]
        self.assertEqual(comments_object.pk, self.comment.pk)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        post_object = response.context['post']
        self.assert_method_for_tests_first_object(post_object)
        self.assertIsInstance(response.context.get('form'), PostForm)

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
        post_two = Post.objects.create(
            author=self.user,
            text='Текст для added correctly group',
            group=self.group_2,
        )
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(
            first_object.pk,
            post_two.pk,
            'Пост найден в некорректной группе')

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей"""
        error_one = 'В БД найден объект которого не должно быть'
        self.assertFalse(Follow.objects.filter(
            user=self.user_2, author=self.user
        ).exists(), error_one)
        self.authorized_client_two.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}
        ))
        error_two = 'В БД не найден ожидаемый объект'
        self.assertTrue(Follow.objects.filter(
            user=self.user_2, author=self.user
        ).exists(), error_two)

    def test_unfollow(self):
        """Авторизованный пользователь может удалять
        других пользователей из своих подписок"""
        Follow.objects.create(
            user=self.user_2,
            author=self.user
        )
        self.authorized_client_two.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user.username}
        ))
        error_one = 'Из БД не был удален ожидаемый объект'
        self.assertFalse(Follow.objects.filter(
            user=self.user_2, author=self.user
        ).exists(), error_one)

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
        response_user_one = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        error_two = f'Пост найден на странице follow у {self.user}'
        self.assertNotEqual(
            response_user_one.context['page_obj'], new_post.pk, error_two
        )


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
                self.assertEqual(
                    len(first_page_response.context['page_obj']),
                    POSTS_PER_PAGE,
                    f'Страница {page}, не прошла проверку 1ой страницы'
                )
                self.assertEqual(
                    len(second_page_response.context['page_obj']),
                    (POSTS_FOR_BULK_CREATE - POSTS_PER_PAGE),
                    f'Страница {page}, не прошла проверку 2ой страницы'
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
        self.assertNotEqual(after_clear_cache.content, after_delete)
