from django.db import models

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    mobile = models.CharField(max_length=11,verbose_name="手机号")
    email_active = models.BooleanField(default=False,verbose_name="邮箱激活状态")

    class Meta:
        db_table = "tb_users"