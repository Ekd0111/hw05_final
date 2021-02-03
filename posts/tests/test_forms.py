import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        user = get_user_model()
        cls.guest_client = Client()
        cls.user = user.objects.create_user(username='Test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        small_01_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                        b'\x01\x00\x80\x00\x00\x00\x00\x00'
                        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                        b'\x0A\x00\x3B')
        cls.uploaded = SimpleUploadedFile(
            name='small_01.gif',
            content=small_01_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        '''Форма после валидации создает новую запись.'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст',
            'group': self.group.id,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count+1)
        self.assertTrue(Post.objects.filter(text=self.post.text,
                        image=self.post.image).exists())

    def test_post_edit(self):
        """При изменении поста через форму post_edit изменяется запись в базе.
        """
        form_data = {
            'text': 'Текст1',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('post_edit', args=[self.user.username, self.post.id]),
            data=form_data,
            follow=True,
        )
        post_count = Post.objects.count()
        self.post.refresh_from_db()
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])
        self.assertEqual(response.status_code, 200)
