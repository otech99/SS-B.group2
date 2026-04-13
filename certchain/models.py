from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import random
import string
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    """Manager per CustomUser."""

    def create_user(self, username, email, password, role, **extra_fields):
        if not email:
            raise ValueError('Email obbligatoria')
        email = self.normalize_email(email)
        user  = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        return self.create_user(
            username=username,
            email=email,
            password=password,
            role=CustomUser.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
            **extra_fields
        )

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Utente con ruolo fisso e indice per file JSON."""

    class Role(models.TextChoices):
        ADMIN                = 'ADMIN',                'Amministratore'
        CERTIFYING_AUTHORITY = 'CERTIFYING_AUTHORITY', 'Ente Certificatore'
        STUDENT              = 'STUDENT',              'Studente'
        COMPANY              = 'COMPANY',              'Azienda' # <--- Aggiunta Azienda

    username   = models.CharField(max_length=150, unique=True)
    email      = models.EmailField(unique=True)
    role       = models.CharField(
        max_length=30,
        choices=Role.choices,
        editable=False,
    )
    
    # 🔹 NUOVO CAMPO: Serve per mappare student1 -> s1, student2 -> s2, ecc.
    # Sarà null per Admin, Azienda e Authority.
    student_index = models.PositiveIntegerField(null=True, blank=True, help_text="Indice per i file JSON (es. 1 per s1)")

    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    # Metodi di controllo
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_certifying_authority(self):
        return self.role == self.Role.CERTIFYING_AUTHORITY

    def is_student(self):
        return self.role == self.Role.STUDENT
    
    def is_company(self): # <--- Aggiunto metodo per Azienda
        return self.role == self.Role.COMPANY

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
        
class OTPToken(models.Model):
    """Token OTP per la verifica in due passaggi."""

    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token      = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def is_valid(self):
        expiry = self.created_at + timedelta(minutes=5)
        return not self.is_used and timezone.now() < expiry

    @staticmethod
    def generate_token():
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"OTP per {self.user.username} — {self.token}"