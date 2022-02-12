from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User

SLUG = "testslug"
AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст, длинее 15 символов"
GROUP_TITLE = "Тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
INDEX_URL = reverse("posts:index")
GROUP_LIST_URL = reverse("posts:group_list", args=[SLUG])
LOGIN_URL = reverse("users:login")
POST_CREATE_URL = reverse("posts:post_create")
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{LOGIN_URL}?next={POST_CREATE_URL}"
PROFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])
MISSING_PAGE_URL = ("/missing/")


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.user = User.objects.create_user(username=NOT_AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group,
        )
        cls.COMMENT = reverse("posts:add_comment", args=[cls.post.id])
        cls.FOLLOW_REDIRECT_COMMENT_TO_LOGIN = (
            f"{LOGIN_URL}?next={cls.COMMENT}")
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.FOLLOW_REDIRECT_EDIT_TO_LOGIN = (
            f"{LOGIN_URL}?next={cls.POST_EDIT_URL}")

    def setUp(self):
        self.guest = Client()
        self.another = Client()
        self.another.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.auth_user)
        cache.clear()

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности URL.
        Сервер возращает ожидаемый HTTP status code.
        """
        set = [
            [INDEX_URL, 200, self.author, "author"],
            [GROUP_LIST_URL, 200, self.author, "author"],
            [PROFILE_URL, 200, self.author, "author"],
            [self.POST_DETAIL_URL, 200, self.author, "author"],
            [POST_CREATE_URL, 200, self.author, "author"],
            [self.POST_EDIT_URL, 200, self.author, "author"],
            [POST_CREATE_URL, 302, self.guest, "guest"],
            [self.POST_EDIT_URL, 302, self.guest, "guest"],
            [self.POST_EDIT_URL, 302, self.another, "another"],
            [self.COMMENT, 302, self.guest, "guest"],
            [MISSING_PAGE_URL, 404, self.guest, ""]
        ]
        for url, status_code, client, user in set:
            with self.subTest(url=url, client=user):
                self.assertEqual(
                    client.get(url).status_code,
                    status_code)

    def test_redirect_to_login(self):
        """Перенаправляет анонимного пользователя и не автора поста"""
        urls = [
            [self.guest, POST_CREATE_URL,
                FOLLOW_REDIRECT_CREATE_TO_LOGIN],
            [self.guest, self.COMMENT,
                self.FOLLOW_REDIRECT_COMMENT_TO_LOGIN],
            [self.guest, self.POST_EDIT_URL,
                self.FOLLOW_REDIRECT_EDIT_TO_LOGIN],
            [self.another, self.POST_EDIT_URL,
                self.POST_DETAIL_URL],
        ]
        for client, url, redirect_url in urls:
            with self.subTest(value=redirect_url):
                self.assertRedirects(
                    client.get(url, follow=True),
                    redirect_url)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        template_url_names = {
            INDEX_URL: "posts/index.html",
            GROUP_LIST_URL: "posts/group_list.html",
            PROFILE_URL: "posts/profile.html",
            self.POST_DETAIL_URL: "posts/post_detail.html",
            POST_CREATE_URL: "posts/create_post.html",
            self.POST_EDIT_URL: "posts/create_post.html",
            MISSING_PAGE_URL: "core/404.html",
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address), template
                )
