from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст для метода str',
            author=get_user_model().objects.create(username='test_name'),
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'group': 'Группа',
            'text': 'Текст',
            'pub_date': 'Дата публикации',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Напишите свои мысли тут:)'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)

    def test_str_is_equal_to_text(self):
        """Метод '__str__' совпадает с ожидаемым."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='Текстовое описание',
        )

    def test_str_is_equal_to_title(self):
        """Метод '__str__' совпадает с ожидаемым."""
        group = GroupModelTest.group
        self.assertEqual(str(group), group.title)
