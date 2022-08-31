from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        help_texts = {
            'text': 'Здесь пишут текст поста',
            'group': 'Выберите группу, к которой относится Ваш пост',
            'image': 'Картинка к посту'
        }
        model = Post
        fields = (
            'text',
            'group',
            'image'
        )


class CommentForm(forms.ModelForm):
    class Meta:
        help_texts = {
            'comments_text': 'Текст комментария',
        }
        model = Comment
        fields = (
            'comments_text',
        )
