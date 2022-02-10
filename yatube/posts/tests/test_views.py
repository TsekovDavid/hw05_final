import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, User, Comment
from yatube.settings import POSTS_ON_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


SLUG = "testslug"
SECOND_SLUG = "slugslug"
AUTHOR_USERNAME = "Abraham"
NOT_AUTHOR_USERNAME = "Isaak"
POST_TEXT = "Тестовый текст, длинее 15 символов"
SECOND_TEXT = "Текст второго поста"
GROUP_TITLE = "Тестовая группа"
SECOND_GROUP_TITLE = "Вторая тестовая группа"
GROUP_DESCRIPTION = "Тестовое описание"
SECOND_GGROUP_DESCRIPTION = "Тестовое описание второй группы"
COMMENT_TEXT = "Текст комментария к посту"
POST_CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
FOLLOW_REDIRECT_CREATE_TO_LOGIN = f"{LOGIN_URL}?next={POST_CREATE_URL}"
SECOND_GROUP_LIST_URL = reverse("posts:group_list", args=[SECOND_SLUG])
GROUP_LIST_URL = reverse("posts:group_list", args=[SLUG])
INDEX_URL = reverse("posts:index")
PROFILE_URL = reverse("posts:profile", args=[AUTHOR_USERNAME])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class YatubeViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NOT_AUTHOR_USERNAME)
        cls.auth_user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.group2 = Group.objects.create(
            title=SECOND_GROUP_TITLE,
            slug=SECOND_SLUG,
            description=SECOND_GGROUP_DESCRIPTION
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text=POST_TEXT,
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            text=COMMENT_TEXT,
            post=cls.post,
            author=cls.auth_user,
        )
        cls.POST_DETAIL_URL = reverse("posts:post_detail", args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.another = Client()
        self.another.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.auth_user)
        cache.clear()

    def test_profile_page_show_correct_context(self):
        """Страница автора формируется с корректным контекстом."""
        self.assertEqual(
            self.another.get(PROFILE_URL).context["author"],
            self.post.author)

    def test_group_list_show_correct_context(self):
        """Страница сообщества формируется с корректным контекстом."""
        group = self.another.get(GROUP_LIST_URL).context["group"]
        self.assertEqual(group.id, self.post.group.id)
        self.assertEqual(group.title, self.post.group.title)
        self.assertEqual(group.description, self.post.group.description)
        self.assertEqual(group.slug, self.post.group.slug)

    def test_post_displayed_in_the_correct_pages(self):
        adresses = [
            INDEX_URL,
            GROUP_LIST_URL,
            self.POST_DETAIL_URL,
            PROFILE_URL
        ]
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.another.get(adress)
                if adress == self.POST_DETAIL_URL:
                    post = response.context["post"]
                    self.assertEqual(
                        response.context["comments"][0],
                        self.comment)
                else:
                    post = response.context["page_obj"][0]
                    self.assertEqual(len(response.context["page_obj"]), 1)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(self.post.pk, post.pk)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.image, post.image)

    def test_post_is_not_displayed_in_someone_elses_group(self):
        """Пост не отображается в чужом сообществе."""
        response = self.another.get(SECOND_GROUP_LIST_URL)
        self.assertNotIn(self.post, response.context["page_obj"])

    def test_cache_from_index_page(self):
        page_content = self.guest.get(INDEX_URL).content
        Post.objects.create(
            text=POST_TEXT,
            group=self.group,
            author=self.user
        )
        self.assertEqual(page_content, self.guest.get(INDEX_URL).content)
        cache.clear()
        self.assertNotEqual(page_content, self.guest.get(INDEX_URL).content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.BATCH_SIZE = POSTS_ON_PAGE + 3
        Post.objects.bulk_create(
            Post(author=cls.user, text=f"Текст {i}", group=cls.group)
            for i in range(cls.BATCH_SIZE))

    def setUp(self):
        self.guest_client = Client()

    def test_page_contains_the_correct_number_of_posts(self):
        """Паджинатор выводит правильное количество постов на страницу."""
        POSTS_ON_PAGE_2 = self.BATCH_SIZE - POSTS_ON_PAGE
        set = [
            [INDEX_URL, POSTS_ON_PAGE],
            [PROFILE_URL, POSTS_ON_PAGE],
            [GROUP_LIST_URL, POSTS_ON_PAGE],
            [INDEX_URL + "?page=2", POSTS_ON_PAGE_2],
            [PROFILE_URL + "?page=2", POSTS_ON_PAGE_2],
            [GROUP_LIST_URL + "?page=2", POSTS_ON_PAGE_2],
        ]
        for url, posts_count in set:
            cache.clear()
            response = self.guest_client.get(url)
            self.assertEqual(len(response.context["page_obj"]), posts_count)
