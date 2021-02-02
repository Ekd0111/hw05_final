from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .forms import PostForm, CommentForm
from .models import Post, Group, Comment, Follow

User = get_user_model()
POSTS_PER_PAGE = 10


def index(request):
    """Главная страница."""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    contex = {'page': page, 'paginator': paginator}
    return render(request, 'index.html', contex)


def group_posts(request, slug):
    """Страница группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).all()
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    contex = {'group': group, 'posts': posts,
              'page': page, 'paginator': paginator}
    return render(request, 'group.html', contex)


@login_required
def new_post(request):
    """Страница профайла автора."""
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')
    contex = {'form': form, 'is_edit': False}
    return render(request, 'new.html', contex)


def profile(request, username):
    """Страница профайла автора."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    posts_count = Post.objects.filter(
        author=author).select_related('author').count()
    form = CommentForm(request.POST or None)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()
    contex = {'author': author, 'page': page, 'paginator': paginator,
              'posts_count': posts_count, 'form': form, 'following': following}
    return render(request, 'profile.html', contex)


def post_view(request, username, post_id):
    """Страница с отдельным постом."""
    post = get_object_or_404(Post, author__username=username,
                             id=post_id)
    comments = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    contex = {'post': post, 'author': post.author,
              'comments': comments, 'form': form}
    return render(request, 'post.html', contex)


@login_required
def add_comment(request, username, post_id):
    """Страница с отдельным постом и с формой для комментария."""
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if request.GET or not form.is_valid():
        return render(request, 'post.html', {'post': post_id})
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    form.save()
    return redirect(reverse('post', kwargs={'username': username,
                                            'post_id': post_id}))


@login_required
def post_edit(request, username, post_id):
    """Страница с формой для редактирования поста."""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'new.html', {
        'form': form,
        'post': post,
        'is_edit': True, })


@login_required
def follow_index(request):
    """Страница с постами авторов на которых подписан пользователь."""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'paginator': paginator}
    return render(request, 'follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (Follow.objects.filter(user=request.user,
                              author=author).exists() or
            request.user == author):
        return profile(request, username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception=None):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
