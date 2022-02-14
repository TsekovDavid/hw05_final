import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from posts.models import Group, Post, User, Comment
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR_USERNAME = "Abraham"
POST_TEXT = "Тестовый текст"
GROUP_TITLE = "Тестовая группа"
SLUG = "testslug"
GROUP_DESCRIPTION = "Тестовое описание"
SECOND_GROUP_TITLE = "Вторая тестовая группа"
SECOND_SLUG = "new_group"
SECOND_GROUP_DESCRIPTION = "Тестовое описание второй группы"
PROFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])
POST_CREATE_URL = reverse("posts:post_create")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
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
        cls.form = PostForm()
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.auth_user)

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post_count = Post.objects.count()
        form_data = {
            "text": "Новый текст для поста",
            "group": self.group2.id,
        }
        self.author.post(
            self.POST_EDIT_URL, data=form_data, follow=True)
        refresh_post = self.author.get(
            self.POST_DETAIL_URL).context["post"]
        self.assertEqual(refresh_post.text, form_data["text"])
        self.assertEqual(refresh_post.group.id, form_data["group"])
        self.assertEqual(refresh_post.author, self.post.author)
        self.assertEqual(post_count, Post.objects.count())

    def test_create_post_form(self):
        """Валидная форма создает новый пост."""
        Post.objects.all().delete()
        new_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='new.gif',
            content=new_gif,
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
        self.assertEqual(post.image, f"posts/{uploaded}")

    def test_form_post_create_and_post_edit(self):
        """Формы создания и редкатирования поста корректны."""
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
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
        cls.form = PostForm()
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.COMMENT = reverse("posts:add_comment", args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.auth_user)

    def test_valid_form_creates_comment(self):
        """Валидная форма добавляет комментарий к посту."""
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.author.post(self.COMMENT, data=form_data, follow=True)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.text, form_data["text"])
        self.assertIn(comment, self.author.get(
            self.POST_DETAIL_URL).context["post"].comments.all())

    def test_form_add_comment(self):
        """Форма добавления комментария корректна."""
        self.assertIsInstance(self.author.get(
            self.POST_DETAIL_URL).context.get("form").fields.get("text"),
            forms.fields.CharField)
