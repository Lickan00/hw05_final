from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import User, Post, Group


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='tests_group',
            slug='tests_group',
        )
        cls.user = User.objects.create_user(username='DimaB')
        cls.user_2 = User.objects.create_user(username='Yulia')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(StaticURLTests.user_2)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                error_name: str = f'Ошибка: {adress} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_guest_client_urls_status_200(self):
        """"Проверка url связанных с гостевым пользователем"""
        guest_urls = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.pk}/',
        )
        for url in guest_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                error_response = f'Url {url}, не прошел тест'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_response
                )

    def test_guest_client_urls_status_302(self):
        """Тесты статусов приватных страниц для гостей"""
        urls = (
            f'/posts/{self.post.pk}/edit/',
            '/create/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                error_response = f'У client открылся Url {url}'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND,
                    error_response
                )

    def test_urls_redirect_guest_client(self):
        urls = {
            f'/posts/{self.post.pk}/edit/':
                f'''{reverse("users:login")}?next={reverse("posts:post_edit",
                    kwargs={"post_id": self.post.pk})}''',
            '/create/':
                f'''{reverse("users:login")}?next={reverse(
                    "posts:post_create")}''',
        }
        for page, value in urls.items():
            with self.subTest(page=page):
                response_client = self.client.get(page)
                self.assertRedirects(response_client, value)

    def test_urls_redirect_user_two_edit_someone_post(self):
        response = self.authorized_client_two.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_edit_post_author(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_page(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
