from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        """Возврати понятное отображение заголовка
        в панель администрирования."""
        return self.title


class Post(models.Model):
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name='posts',
                              verbose_name='Группа',
                              )
    text = models.TextField(verbose_name='Текст',
                            help_text='Напишите свои мысли тут:)'
                            )
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True,
                                    )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts')
    image = models.ImageField(
        upload_to='posts/',
        blank=True, null=True,
        verbose_name='Изображение',
        help_text='Вы можете добавить изображение к своему посту',
        )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        """Возврати понятное отображение заголовка
        в панель администрирования."""
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Пост')
    text = models.TextField(verbose_name='Текст',
                            help_text='Что вы хотели добавить или уточнить?')
    created = models.DateTimeField(verbose_name='Дата и время публикации',
                                   auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        """Возврати понятное отображение заголовка
        в панель администрирования."""
        return self.post


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_object')]

    def __str__(self):
        return self.author.username, self.user
