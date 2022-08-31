from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Group, Post, User
from .utils import paginate_page


@cache_page(20)
def index(request):
    template_main = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group')
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template_main, context)


def group_posts(request, slug):
    template_group = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group
    }
    return render(request, template_group, context)


def profile(request, username):
    template_name = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    profile = author.posts.all()
    page_obj = paginate_page(request, profile)
    context = {
        'page_obj': page_obj,
        'author': author
    }
    return render(request, template_name, context)


def post_detail(request, post_id):
    template_name = 'posts/post_detail.html'

    form = CommentForm(request.POST or None)

    post = get_object_or_404(Post, pk=post_id)
    post_comments = Comment.objects.filter(comments_post_id=post_id)
    author = get_object_or_404(User, id=post.author_id)
    context = {
        'form': form,
        'post': post,
        'author': author,
        'post_comments': post_comments,
    }
    return render(request, template_name, context)


@login_required
def post_create(request):
    template_name = 'posts/create_post.html'
    form = PostForm(
        request.POST,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    context = {
        'form': form,
        'is_edit': False
    }
    return render(request, template_name, context)


@login_required
def post_edit(request, post_id):
    template_name = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:profile', post.author)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    #is_edit = post
    if form.is_valid():
        post = form.save()
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, template_name, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.comments_author = request.user
        comment.comments_post = post
        comment.save()

    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, posts)

    return render(request, 'posts/follow.html', {'page_obj': page_obj})