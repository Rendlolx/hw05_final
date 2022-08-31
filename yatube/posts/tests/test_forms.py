import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        img_jpeg = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        upload_img = SimpleUploadedFile(
            name='img_jpeg',
            content=img_jpeg,
            content_type='image/jpeg'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.user,
            image=upload_img
        )
        
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Неавторизованный клиент"""
        self.guest_client = Client()

        """Авторизованный юзер"""
        self.user = User.objects.create_user(username='Sereja')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        """Автор"""
        self.author_client = Client()
        self.author_client.force_login(PostCreateFormTests.post.author)

    def test_create_post(self):
        post_count = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_create'),
            data={
                'text': PostCreateFormTests.post.text,
                'group': PostCreateFormTests.group.id,
                'image': PostCreateFormTests.post.image
            },
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)

        post = Post.objects.first()
        self.assertEqual(post.text, PostCreateFormTests.post.text)
        self.assertEqual(post.author, PostCreateFormTests.post.author)
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.image, PostCreateFormTests.post.image)

    def test_post_edit(self):
        post_count = Post.objects.count()
        post = Post.objects.create(
            text=PostCreateFormTests.post.text,
            author=PostCreateFormTests.post.author,
            group=PostCreateFormTests.group
        )
        new_post_text = PostCreateFormTests.post.text
        new_group = Group.objects.create(
            title=PostCreateFormTests.group.title,
            slug='slug_2',
            description=PostCreateFormTests.group.description
        )

        self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostCreateFormTests.post.id}'}),
            data={
                'text': new_post_text,
                'group': new_group.id
            },
            follow=True,
        )

        self.assertEqual(Post.objects.count(), post_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, new_post_text)
        self.assertEqual(post.author, PostCreateFormTests.post.author)
        self.assertEqual(post.group.title, new_group.title)

    def test_create_post_non_authorized_client(self):
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data = {
                'text': PostCreateFormTests.post.text,
                'group': PostCreateFormTests.group.id,
                'image': PostCreateFormTests.post.image
            },
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)

        self.assertRedirects(response, f'/auth/login/?next=/create/')