from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, Follow

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
    post_list = group.posts.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    contex = {'group': group,
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
    is_following = False
    is_following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    contex = {'author': author, 'page': page, 'paginator': paginator,
              'is_following': is_following}
    return render(request, 'profile.html', contex)


def post_view(request, username, post_id):
    """Страница с отдельным постом."""
    post = get_object_or_404(Post, author__username=username,
                             id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    contex = {'post': post, 'author': post.author,
              'comments': comments, 'form': form}
    return render(request, 'post.html', contex)


@login_required
def add_comment(request, username, post_id):
    """Страница с отдельным постом и с формой для комментария."""
    post = get_object_or_404(Post, author__username=username,
                             id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.post = post
        form.save()
    return redirect('post', username, post_id)


@login_required
def post_edit(request, username, post_id):
    """Страница с формой для редактирования поста."""
    # Если пользователь - не автор, то он не будет видеть кнопку
    # "редактировать" и, соответсвенно, не сможет перейти на страницу
    # с формой редактирования.
    # Таким образом, эта проверка ({% if user == post.author %}) реализована
    # прямо в шаблоне "blok_post.html".
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
    if author != request.user and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception=None):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
