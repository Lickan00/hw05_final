from django.test import TestCase

from ..models import Group, Post, User
from ..constants import TEXT_BACK_LIMIT


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        check_list = {
            self.group: self.group.title,
            self.post: self.post.text[:TEXT_BACK_LIMIT],
        }
        for key, value in check_list.items():
            with self.subTest(key=key):
                error_assert = 'Вывод __str__ работает не корректно'
                self.assertEqual(str(key), value, error_assert)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_verboses = {
            'text': 'text',
            'pub_date': 'pub_date',
            'author': 'author',
            'group': 'group',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).verbose_name, expected
                )
