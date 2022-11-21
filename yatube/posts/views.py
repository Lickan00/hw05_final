from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from .utils import get_page_context


@cache_page(20, key_prefix='index_page')
def index(request):
    """Вью для вывода главной страницы с помощью генерации модели Post"""
    context = get_page_context(Post.objects.all(), request)

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """"Вью для вывода страницы group/ с помощью модели Group"""
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
    }
    context.update(get_page_context(group.posts.all(), request))

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Здесь код запроса к модели и создание словаря контекста"""
    author: author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    context = {
        'author': author,
        'posts': posts,
        'following': following,
    }
    context.update(get_page_context(author.posts.all(), request))

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Здесь код запроса к модели и создание словаря контекста"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', username=request.user.username)

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    elif request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'post': post,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """"Страница подписок"""
    follow = Post.objects.filter(author__following__user=request.user)
    context = get_page_context(follow.all(), request)

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Дизлайк, отписка"""
    user_follower = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    )
    user_follower.delete()
    return redirect("posts:profile", username=username)
