from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import CreationForm, PasswordChangeForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:main')
    template_name = 'users/signup.html'


class ChangePassword(UpdateView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('posts:main')
    template_name = 'users/password_change_form.html'
