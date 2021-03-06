from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from string import ascii_letters
from utils.date_convertor import gregorian_to_shamsi
from django.utils import timezone
import random


class UserManager(BaseUserManager):
    use_in_migrations = True
    def create_user(self, username, phone, password, name, introducer):
        invite_code = ''.join(random.choice(ascii_letters) for i in range(10))
        while user.objects.filter(invite_code=invite_code):
            invite_code = ''.join(random.choice(ascii_letters) for i in range(10))
        User = self.model(username=username, phone=phone, invite_code=invite_code, name=name)
        User.set_password(password)
        User.introducer = introducer
        User.shamsi_joined_date = gregorian_to_shamsi(timezone.now())
        User.save(using=self._db)
        return User
    def create_superuser(self, username , password):
        if password is None:
            raise TypeError('Superusers must have a password.')
        User = self.create_user(username, '0990', 'mr@gmail.com','4420888024a')
        User.is_superuser = True
        User.is_staff = True
        User.is_admin = True
        User.save()
        return User
 
class user(AbstractUser): 
    phone = models.CharField(max_length=15, unique=True)
    verified_phone = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)
    verified_email = models.BooleanField(default=False)
    verify_code = models.IntegerField(null=True, blank=True)
    verify_code_time = models.DateTimeField(null=True, blank=True)
    invite_code = models.CharField(max_length=10, unique=True)
    introducer = models.ForeignKey('user', null=True, blank=True,related_name='invited_set' , on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    image = models.ImageField(upload_to='profiles', default='profiles/default-user.jpg') 
    followings = models.ManyToManyField('user', related_name='followers') 
    first_name = None
    last_name = None
    name = models.BinaryField(default=b'')
    shamsi_joined_date = models.CharField(max_length=11, null=True)
    objects = UserManager()

