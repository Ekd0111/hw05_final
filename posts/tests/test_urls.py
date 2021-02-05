from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = get_user_model().objects.create(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='Текстовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self):
        self.guest_client = Client()

        User = get_user_model()
        self.user_other = User.objects.create_user(username='Test_name_other')
        self.authorized_client_other = Client()
        self.authorized_client_other.force_login(self.user_other)

        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(URLTests.author)

    def test_urls_exists_at_desired_location(self):
        """Проверка доступности URL-адреса для неавторизованного польз-ля."""
        url_adresses = {
            '/500/': 500,
            '/404/status=404': 404,
            '/': 200,
            '/group/test-group/': 200,
            '/new/': 302,
            '/follow/': 302,
            f'/{self.post.author.username}/follow/': 302,
            f'/{self.post.author.username}/unfollow/': 302,
            f'/{self.post.author.username}/': 200,
            f'/{self.post.author.username}/{self.post.id}/': 200,
            f'/{self.post.author.username}/{self.post.id}/edit/': 302,
            f'/{self.post.author.username}/{self.post.id}/comment/': 302,
        }
        for adress, code in url_adresses.items():
            with self.subTest(url=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_exists_at_uthorized_client_author(self):
        """Проверка доступности URL-адреса для авторизованый клиент - автор."""
        url_adresses = {
            '/': 200,
            '/group/test-group/': 200,
            '/new/': 200,
            f'/{self.post.author.username}/': 200,
            f'/{self.post.author.username}/{self.post.id}/': 200,
            f'/{self.post.author.username}/{self.post.id}/edit/': 200,
        }
        for url, code in url_adresses.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_exists_at_authorized_client_other(self):
        """Проверка доступности URL-адреса для авторизованный
        клиент - не автор.
        """
        url_adresses = {
            '/': 200,
            '/group/test-group/': 200,
            '/new/': 200,
            f'/{self.post.author.username}/': 200,
            f'/{self.post.author.username}/{self.post.id}/': 200,
            f'/{self.post.author.username}/{self.post.id}/edit/': 302,
        }
        for adress, code in url_adresses.items():
            with self.subTest(url=adress):
                response = self.authorized_client_other.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/500/': 'misc/500.html',
            '/404/status=404': 'misc/404.html',
            '/': 'index.html',
            '/group/test-group/': 'group.html',
            f'/{self.post.author.username}/{self.post.id}/edit/': 'new.html',
            '/new/': 'new.html',
            f'/{self.post.author.username}/': 'profile.html',
            f'/{self.post.author.username}/{self.post.id}/': 'post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)
