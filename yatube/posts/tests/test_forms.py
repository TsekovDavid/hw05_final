import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст"
COMMENT_TEXT = "Текст нового коментария"
GROUP_TITLE = "Тестовая группа"
SLUG = "testslug"
GROUP_DESCRIPTION = "Тестовое описание"
SECOND_GROUP_TITLE = "Вторая тестовая группа"
SECOND_SLUG = "new_group"
SECOND_GROUP_DESCRIPTION = "Тестовое описание второй группы"
COMMENT_FORM_DATA = {'text': COMMENT_TEXT}
PROFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])
POST_CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{LOGIN_URL}?next={POST_CREATE_URL}"
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
        cls.PICTURE1 = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif')
        cls.PICTURE2 = SimpleUploadedFile(
            name='picture2.gif',
            content=SMALL_GIF,
            content_type='image/gif')
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group,
            image=cls.PICTURE1
        )
        cls.form_data = {
            "text": "Новый текст для поста",
            "group": cls.group2.id,
            "image": cls.PICTURE2
        }
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.FOLLOW_REDIRECT_EDIT_TO_LOGIN = (
            f"{LOGIN_URL}?next={cls.POST_EDIT_URL}")
        cls.author = Client()
        cls.guest = Client()
        cls.another = Client()
        cls.author.force_login(cls.auth_user)
        cls.another.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_edit_by_anonym(self):
        """Аноним и не автор поста не могут его редактировать."""
        set = [
            [self.guest, self.FOLLOW_REDIRECT_EDIT_TO_LOGIN],
            [self.another, self.POST_DETAIL_URL],
        ]
        for client, redirect_url in set:
            with self.subTest(client=get_user(client).username):
                response = client.post(
                    self.POST_EDIT_URL, data=self.form_data, follow=True)
                self.assertRedirects(response, redirect_url)
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.author, self.post.author)

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post_count = Post.objects.count()
        response = self.author.post(
            self.POST_EDIT_URL, data=self.form_data, follow=True)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = self.author.get(self.POST_DETAIL_URL).context.get("post")
        self.assertEqual(post.text, self.form_data["text"])
        self.assertEqual(post.group.id, self.form_data["group"])
        self.assertEqual(post.author, self.post.author)
        picture_name = post.image.name.split('/')[1]
        self.assertEqual(picture_name, self.form_data["image"].name)
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
        picture_name = post.image.name.split('/')[1]
        self.assertEqual(picture_name, form_data["image"].name)

    def test_create_post_from_anonym(self):
        """Анонимный пользователь не может создать пост."""
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
        response = self.guest.post(
            POST_CREATE_URL, data=form_data, follow=True)
        self.assertRedirects(response, FOLLOW_REDIRECT_CREATE_TO_LOGIN)
        self.assertEqual(Post.objects.count(), 0)

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
        cls.FOLLOW_REDIRECT_COMMENT_TO_LOGIN = (
            f"{LOGIN_URL}?next={cls.COMMENT_URL}")
        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(cls.auth_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_comment_from_anonym(self):
        """Анонимный пользователь не может написать комментарий к посту."""
        Comment.objects.all().delete()
        response = self.guest.post(
            self.COMMENT_URL, data=COMMENT_FORM_DATA, follow=True)
        self.assertRedirects(response, self.FOLLOW_REDIRECT_COMMENT_TO_LOGIN)
        self.assertEqual(
            Comment.objects.count(), 0)

    def test_valid_form_creates_comment(self):
        """Валидная форма добавляет комментарий к посту."""
        Comment.objects.all().delete()
        response = self.author.post(
            self.COMMENT_URL, data=COMMENT_FORM_DATA, follow=True)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.text, COMMENT_FORM_DATA["text"])
        self.assertEqual(comment.author, self.auth_user)
        self.assertEqual(comment.post, self.post)

    def test_form_add_comment(self):
        """Форма добавления комментария корректна."""
        self.assertIsInstance(self.author.get(
            self.POST_DETAIL_URL).context.get("form").fields.get("text"),
            forms.fields.CharField)
