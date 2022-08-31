from django.db import models


class ChangePasswordAfterReset(models.Model):
    new_pass = models.CharField(max_length=40)
    new_pass_confirm = models.CharField(max_length=40)
