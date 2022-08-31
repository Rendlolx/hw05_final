from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        """Неавторизованный юзер"""
        self.guest_client = Client()

        """Авторизованный юзер"""
        self.user = User.objects.create_user(username='Sereja')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        """Автор поста"""
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.post.author)

    def test_guest_client_urls(self):
        dict_urls = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTest.post.author}/': HTTPStatus.OK,
            f'/posts/{PostURLTest.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for url, status_code in dict_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_authtorized_user(self):
        dict_urls = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTest.post.author}/': HTTPStatus.OK,
            f'/posts/{PostURLTest.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.OK
        }
        for url, status_code in dict_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_author_get_url(self):
        dict_urls = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTest.post.author}/': HTTPStatus.OK,
            f'/posts/{PostURLTest.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.OK,
            f'/posts/{PostURLTest.post.id}/edit/': HTTPStatus.OK
        }
        for url, status_code in dict_urls.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_redirect_auth_user_to_post_detail(self):
        """Страница редактирования поста авторизованного пользователя
        перенаправляет на сам пост, при условии,
        что пользователь != автор поста
        """
        response = self.authorized_client.get(
            f'/posts/{PostURLTest.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/profile/{PostURLTest.post.author}/'
        )

    def test_redirect_non_auth_user_to_login(self):
        """Страница /posts/<post_id>/edit перенаправляет неавторизованного
        пользователя на страницу логирования.
        """
        response = self.guest_client.get(
            f'/posts/{PostURLTest.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTest.post.id}/edit/'
        )

    def test_correct_templates_in_page(self):
        dict_templates = {
            '/': 'posts/index.html',
            f'/group/{PostURLTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTest.post.author}/': 'posts/profile.html',
            f'/posts/{PostURLTest.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTest.post.id}/edit/': 'posts/create_post.html'
        }
        for url, template in dict_templates.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
