from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("A phone number is required.")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("user_type", User.UserType.ADMIN)
        extra_fields.setdefault("review_status", User.ReviewStatus.APPROVED)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class UserType(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        EMPLOYER = "employer", "Employer"
        ADMIN = "admin", "Admin"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    class ReviewStatus(models.TextChoices):
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    phone = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.EMPLOYEE,
    )
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.UNDER_REVIEW,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    skills = models.ManyToManyField(Skill, related_name="employee_profiles", blank=True)
    preferred_counties = models.JSONField(default=list, blank=True)
    bio = models.TextField()
    id_front = models.ImageField(upload_to="employee_documents/id_fronts/")
    id_back = models.ImageField(upload_to="employee_documents/id_backs/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} profile"


class EmployerProfile(models.Model):
    class EmployerType(models.TextChoices):
        HOUSEHOLD = "household", "Household"
        COMPANY = "company", "Company"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer_profile",
    )
    employer_type = models.CharField(max_length=20, choices=EmployerType.choices)
    email = models.EmailField(unique=True)
    location = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    company_registration_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} employer profile"


class SignupOTP(models.Model):
    class Purpose(models.TextChoices):
        EMPLOYEE_SIGNUP = "employee_signup", "Employee signup"
        PASSWORD_RESET = "password_reset", "Password reset"

    phone = models.CharField(max_length=20)
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["phone", "purpose", "-created_at"]),
        ]

    def has_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone} - {self.purpose}"


class EmployeeSignupApplication(models.Model):
    class Status(models.TextChoices):
        OTP_PENDING = "otp_pending", "OTP pending"
        OTP_VERIFIED = "otp_verified", "OTP verified"
        PERSONAL_COMPLETE = "personal_complete", "Personal complete"
        WORK_COMPLETE = "work_complete", "Work complete"
        DOCUMENTS_COMPLETE = "documents_complete", "Documents complete"
        SUBMITTED = "submitted", "Submitted"

    phone = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OTP_PENDING,
    )
    full_name = models.CharField(max_length=255, blank=True)
    national_id = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=User.Gender.choices, blank=True)
    password_hash = models.CharField(max_length=128, blank=True)
    skills = models.ManyToManyField(Skill, related_name="employee_applications", blank=True)
    preferred_counties = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    id_front = models.ImageField(upload_to="employee_applications/id_fronts/", null=True, blank=True)
    id_back = models.ImageField(upload_to="employee_applications/id_backs/", null=True, blank=True)
    submitted_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="signup_application",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Employee application: {self.phone}"
