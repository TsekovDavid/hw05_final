import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import IMAGE_DIRECTORY, Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст"
GROUP_TITLE = "Тестовая группа"
SLUG = "testslug"
GROUP_DESCRIPTION = "Тестовое описание"
SECOND_GROUP_TITLE = "Вторая тестовая группа"
SECOND_SLUG = "new_group"
SECOND_GROUP_DESCRIPTION = "Тестовое описание второй группы"
PROFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])
POST_CREATE_URL = reverse("posts:post_create")
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
        cls.group2 = Group.objects.create(
            title=SECOND_GROUP_TITLE,
            slug=SECOND_SLUG,
            description=SECOND_GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif')
        cls.form_data = {
            "text": "Новый текст для поста",
            "group": cls.group2.id,
            "image": cls.uploaded
        }
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.author = Client()
        cls.guest = Client()
        cls.another = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author.force_login(self.auth_user)
        self.another.force_login(self.user)

    def test_post_edit_by_anonym(self):
        """Аноним и не автор поста не могут его редактировать."""
        clients = [self.another, self.guest]
        for client in clients:
            with self.subTest(client=get_user(client).username):
                client.post(
                    self.POST_EDIT_URL, data=self.form_data, follow=True)
                post = client.get(
                    self.POST_DETAIL_URL).context["post"]
            self.assertEqual(post.text, self.post.text)

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post_count = Post.objects.count()
        self.author.post(
            self.POST_EDIT_URL, data=self.form_data, follow=True)
        post = self.author.get(self.POST_DETAIL_URL).context["post"]
        self.assertEqual(post.text, self.form_data["text"])
        self.assertEqual(post.group.id, self.form_data["group"])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image, f"{IMAGE_DIRECTORY}{self.uploaded}")
        self.assertEqual(post_count, Post.objects.count())

    def test_create_post_form(self):
        """Валидная форма создает новый пост."""
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='new.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            "text": "Тестовый текст 123",
            "group": self.group.id,
            "image": uploaded
        }
        response = self.author.post(
            POST_CREATE_URL,
            data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.all()[0]
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.author, self.auth_user)
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.image, f"{IMAGE_DIRECTORY}{uploaded}")
        self.guest.post(POST_CREATE_URL, data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), 1)

    def test_form_post_create_and_post_edit(self):
        """Формы создания и редкатирования поста корректны."""
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField
        }
        urls = (self.POST_EDIT_URL, POST_CREATE_URL)
        for url in urls:
            response = self.author.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get("form").fields.get(value)
                    self.assertIsInstance(form_field, expected)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.COMMENT_URL = reverse("posts:add_comment", args=[cls.post.id])
        cls.guest = Client()
        cls.author = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author.force_login(self.auth_user)

    def test_valid_form_creates_comment(self):
        """Валидная форма добавляет комментарий к посту."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'Текст комментария',
        }
        self.guest.post(self.COMMENT_URL, data=form_data, follow=True)
        self.assertEqual(
            Comment.objects.count(), 0,
            "Анонимный пользователь добавил комментарий.")
        response = self.author.post(
            self.COMMENT_URL, data=form_data, follow=True)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.author, self.auth_user)
        self.assertEqual(comment.post, self.post)

    def test_form_add_comment(self):
        """Форма добавления комментария корректна."""
        self.assertIsInstance(self.author.get(
            self.POST_DETAIL_URL).context.get("form").fields.get("text"),
            forms.fields.CharField)

