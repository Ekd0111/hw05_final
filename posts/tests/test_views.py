import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Post, Group
from posts.views import POSTS_PER_PAGE

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        User = get_user_model()
        cls.user = User.objects.create(username='Test_user')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug',
        )
        cls.group_01 = Group.objects.create(
            title='Заголовок1',
            description='Текст1',
            slug='test-slug-1',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_pages_uses_correct_template(self):
        """Посты выводятся во всех шаблонах корректно."""
        template_pages_names = {
            'group.html': reverse('group_posts',
                                  kwargs={'slug': self.group.slug}),
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
        }
        for template, reverse_name in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_page_show_correct_context_index(self):
        """Форма нового поста выводится корректно."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Форма редактирования поста выводится корректно."""
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': self.user, 'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        """Главная страница выводится корректно."""
        response = self.authorized_client.get(reverse('index'))
        expected_data = {
            self.post.text: response.context.get('page')[0].text,
            self.post.author.username:
            response.context.get('page')[0].author.username,
            self.post.image: response.context.get('page')[0].image,
        }
        for expected, value in expected_data.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_group_page_show_correct_context(self):
        """Страница группы выводится корректно."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': self.group.slug}))
        expected_data = {
            self.group.title: response.context.get('group').title,
            self.group.slug: response.context.get('group').slug,
            self.group.description: response.context.get('group').description,
            self.post.image: response.context.get('page')[0].image,
        }
        for expected, value in expected_data.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_profile_page_show_correct_context(self):
        """Страница профайла автора выводится корректно."""
        response = self.authorized_client.get(
            reverse('profile',
                    kwargs={'username': self.user})
        )
        expected_data = {
            self.post.text: response.context.get('page')[0].text,
            self.post.author.username:
            response.context.get('page')[0].author.username,
            self.post.image: response.context.get('page')[0].image,
        }
        for expected, value in expected_data.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_with_group_in_other_group_slug(self):
        """Пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': self.group_01.slug}))
        self.assertNotIn(self.post, response.context['page'])

    def test_page_not_found_page_uses_correct_template(self):
        """При запросе к posts:page_not_found применяется шаблон misc/404.
        html.
        """
        response = self.authorized_client.get(reverse('404'))
        self.assertTemplateUsed(response, 'misc/404.html')

    def test_server_error_page_uses_correct_template(self):
        """При запросе к posts:server_error применяется шаблон misc/500.
        html.
        """
        response = self.authorized_client.get(reverse('500'))
        self.assertTemplateUsed(response, 'misc/500.html')

    def test_cache_index(self):
        """Проверка кэширования главной страницы."""
        response = self.authorized_client.get(reverse('index'))
        Post.objects.create(
            author=self.post.author,
            group=self.group,
            text='test_text',
            )
        response2 = self.authorized_client.get(reverse('index'))
        self.assertHTMLEqual(str(response), str(response2))
        cache.clear()
        response3 = self.authorized_client.get(reverse('index'))
        self.assertHTMLEqual(str(response), str(response3))

    def test_new_post_not_appear_not_follower(self):
        """Новая запись не появится в ленте не подписчика."""
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertFalse(response.context['page'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(username='Test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug',
        )
        cls.post_count = 13
        cls.posts = Post.objects.bulk_create([Post(
            text=str(post),
            author=cls.user,
            group=cls.group,
        ) for post in range(cls.post_count)])

    def test_first_page_containse_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list),
                         POSTS_PER_PAGE)

    def test_second_page_containse_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list),
                            (self.post_count - POSTS_PER_PAGE))
