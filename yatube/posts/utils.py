from django.core.paginator import Paginator

from posts.constants import POSTS_PER_PAGE


def get_page_context(posts, request):
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj,
    }
