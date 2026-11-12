from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self._create(email, password, **extra)


class EmailOTP(models.Model):
    """One-time 6-digit code sent by email. Only a keyed hash of the code is stored."""

    SIGNUP, LOGIN = 'signup', 'login'

    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=10)
    code_hash = models.CharField(max_length=64)
    # signup only: the details to create the account with once the code is confirmed
    name = models.CharField(max_length=120, blank=True)
    password_hash = models.CharField(max_length=256, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.purpose} code for {self.email}'


class User(AbstractUser):
    """Email is the login. `first_name` stores the member's full name."""

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']
    objects = UserManager()

    @property
    def display_name(self):
        return self.first_name or self.email.split('@')[0]

    def __str__(self):
        return self.email
