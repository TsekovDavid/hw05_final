from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import POSTS_ON_PAGE
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def paginator_view(request, post_list):
    return Paginator(post_list, POSTS_ON_PAGE).get_page(
        request.GET.get("page"))


@cache_page(20)
def index(request):
    return render(request, "posts/index.html", {
        "page_obj": paginator_view(request, Post.objects.all())
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, "posts/group_list.html", {
        "group": group,
        "page_obj": paginator_view(request, group.posts.all())
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, "posts/profile.html", {
        "author": author,
        "page_obj": paginator_view(request, author.posts.all()),
        "following": (
            request.user != author
            and request.user.is_authenticated
            and Follow.objects.filter(
                author=author,
                user=request.user
            ).exists())
    })


def post_detail(request, post_id):
    return render(request, "posts/post_detail.html", {
        "post": get_object_or_404(Post, id=post_id),
        "form": CommentForm(request.POST or None),
    })


@login_required
def post_create(request):
    template = "posts/create_post.html"
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, template, {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    context = {
        "form": form,
        "post_id": post_id,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(request, "posts/follow.html", {
        "page_obj": paginator_view(
            request,
            Post.objects.filter(author__following__user=request.user))
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username).delete()
    return redirect('posts:profile', username=username)
