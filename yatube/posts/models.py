from django.contrib.auth import get_user_model
from django.db import models

IMAGE_DIRECTORY = 'posts/'

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Название сообщества", max_length=200)
    slug = models.SlugField("Идентификатор страницы", unique=True)
    description = models.TextField("Описание сообщества")

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст")
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        related_name="posts",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="posts",
    )
    image = models.ImageField(
        'Картинка',
        upload_to=IMAGE_DIRECTORY,
        blank=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        related_name="comments",
        verbose_name="Пост",
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="comments",
    )
    text = models.TextField(
        verbose_name="Текст комментария",
        blank=True)
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата комментария",
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name="Подписчик",
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name="Тот на кого подписываются",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "author"),
                name="unique follow")
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.author.username}"
