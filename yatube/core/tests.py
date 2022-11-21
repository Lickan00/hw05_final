from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    """404 отдаёт кастомный шаблон."""
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        error_name = 'Ошибка: страница 404 использует не кастомный шаблон'
        self.assertTemplateUsed(response, 'core/404.html', error_name)
