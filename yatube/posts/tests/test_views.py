from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()


class PostViewsTest(TestCase):
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
            text='Тестовый пост',
            group=cls.group,
            comment='Текст комментария',
        )

    def setUp(self):
        cache.clear()
        """Неавторизованный юзер"""
        self.guest_client = Client()

        """Авторизованный юзер"""
        self.user = User.objects.create_user(username='Sereja')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        """Автор"""
        self.author_client = Client()
        self.author_client.force_login(PostViewsTest.post.author)

    def test_right_template_in_views(self):
        dict_templates = {
            reverse('posts:main'): 'posts/index.html',
            reverse(
                'posts:group', kwargs={'slug': PostViewsTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': PostViewsTest.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': PostViewsTest.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': PostViewsTest.post.id}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in dict_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, PostViewsTest.user)
        self.assertEqual(post.text, PostViewsTest.post.text)
        self.assertEqual(post.group, PostViewsTest.post.group)
        self.assertEqual(post.image, PostViewsTest.post.image)

    def test_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:main'))
        self.check_context_contains_page_or_post(response.context)

    def test_page_group_show_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:group',
            kwargs={'slug': PostViewsTest.group.slug})
        )
        self.check_context_contains_page_or_post(response.context)

        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, PostViewsTest.group.title)
        self.assertEqual(group.description, PostViewsTest.group.description)

    def test_page_profile_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewsTest.post.author})
        )
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], PostViewsTest.user)

    def test_page_one_post_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewsTest.post.id})
        )
        self.check_context_contains_page_or_post(response.context, post=True)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], PostViewsTest.user)

    def test_create_and_page_show_correct_context(self):
        list_urls = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit', kwargs={'post_id': PostViewsTest.post.id}
            )
        ]
        for url in list_urls:
            response = self.author_client.get(url)

            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], PostForm)

            self.assertIn('is_edit', response.context)
            is_edit = response.context['is_edit']
            self.assertIsInstance(is_edit, bool)

            if url == reverse('posts:post_create'):
                self.assertEqual(is_edit, False)
            else:
                self.assertEqual(is_edit, True)

    def test_comment_on_post_page(self):
        comment_count = Comment.objects.count()
        form_data = {
            'comments_text': f'{PostViewsTest.post.comment}'
        }
        response = self.author_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostViewsTest.post.id}
            ),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewsTest.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                comments_text=form_data['comments_text'],
            ).exists()
        )
        self.assertEqual(comment.comments_author, PostViewsTest.user)

    def test_create_comment_guest_client(self):
        response = self.guest_client.get(
            f'/posts/{PostViewsTest.post.id}/comment/'
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostViewsTest.post.id}/comment/'
        )

    def test_cache_index(self):
        '''Проверка кэша главной страницы.'''
        response = self.author_client.get(reverse('posts:main'))
        posts = response.content
        Post.objects.create(
            text=PostViewsTest.post.text,
            author=PostViewsTest.post.author,
            group=PostViewsTest.group,
            comment=PostViewsTest.post.comment
        )
        response_1 = self.author_client.get(reverse('posts:main'))
        posts_1 = response_1.content
        self.assertEqual(posts_1, posts)
        cache.clear()
        response_2 = self.author_client.get(reverse('posts:main'))
        posts_2 = response_2.content
        self.assertNotEqual(posts_1, posts_2)


class PaginatorViewsTest(TestCase):
    """Тестирование пагинатора"""
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_test',
            description='Тестовое описание',
        )
        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост' + str(i),
                group=cls.group
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
        self.author_client.force_login(PaginatorViewsTest.post.author)

    def test_paginator_in_page_and_count(self):
        first_page_amount = 10
        second_page_amount = 3

        pages = (
            (1, first_page_amount),
            (2, second_page_amount)
        )

        list_pag = [
            reverse('posts:main'),
            reverse(
                'posts:group',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.post.author}
            )
        ]

        for url in list_pag:
            for page, count in pages:
                with self.subTest(page=page):
                    response = self.guest_client.get(url, {'page': page})
                    self.assertEqual(
                        len(response.context['page_obj']), count
                    )
