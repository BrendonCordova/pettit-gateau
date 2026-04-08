from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from apps.base.models import BaseModel

class CustomerManager(BaseUserManager):
    """
    Customized manager for creating users using email as a unique identifier.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O endereço de e-mail é obrigatório.")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Teaches Django how to create a superuser from the terminal without asking for a username.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('superuser precisa ter is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)
    
class Customer(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom User Template focused on E-commerce.
    Replaces the default Username with Email.
    """
    email = models.EmailField(unique=True, verbose_name="E-mail")
    first_name = models.CharField(max_length=50, verbose_name="Nome")
    last_name = models.CharField(max_length=50, verbose_name="Sobrenome")
    tax_id = models.CharField(max_length=14, unique=True, null=True, blank=True, verbose_name="CPF")
    birth_date = models.DateField(null=True, blank=True, verbose_name='Data de nascimento')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")

    # is_active = models.BooleanField(default=True, verbose_name="Ativo")
    is_staff = models.BooleanField(default=False, verbose_name="Membro da equipe")

    objects = CustomerManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "Cliente / Usuário"
        verbose_name_plural = "Clientes / Usuários"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - ({self.email})"
