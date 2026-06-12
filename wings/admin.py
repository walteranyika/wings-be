from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmployeeProfile, EmployeeSignupApplication, EmployerProfile, SignupOTP, Skill, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["phone"]
    list_display = ["phone", "full_name", "user_type", "review_status", "is_active", "is_staff"]
    list_filter = ["user_type", "review_status", "is_active", "is_staff"]
    search_fields = ["phone", "full_name", "national_id"]
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("full_name", "national_id", "date_of_birth", "gender")}),
        ("Status", {"fields": ("user_type", "review_status", "is_active", "is_staff")}),
        ("Permissions", {"fields": ("is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2", "user_type", "review_status", "is_active", "is_staff"),
            },
        ),
    )


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "updated_at"]
    search_fields = ["user__phone", "user__full_name", "user__national_id"]
    filter_horizontal = ["skills"]


@admin.register(EmployeeSignupApplication)
class EmployeeSignupApplicationAdmin(admin.ModelAdmin):
    list_display = ["phone", "full_name", "status", "created_at", "updated_at"]
    search_fields = ["phone", "full_name", "national_id"]
    list_filter = ["status", "gender"]
    filter_horizontal = ["skills"]


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "employer_type", "email", "location", "created_at", "updated_at"]
    search_fields = [
        "user__phone",
        "user__full_name",
        "email",
        "company_name",
        "company_registration_number",
    ]
    list_filter = ["employer_type"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(SignupOTP)
class SignupOTPAdmin(admin.ModelAdmin):
    list_display = ["phone", "purpose", "is_verified", "expires_at", "created_at"]
    search_fields = ["phone"]
    list_filter = ["purpose", "is_verified"]
