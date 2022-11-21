from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Открываем страницу об авторе"""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Открываем страницу о технологиях"""
    template_name = 'about/tech.html'
