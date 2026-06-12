from django.urls import path

from .views import (
    CompanyEmployerSignupView,
    EmployeeSignupIDDocumentsView,
    EmployeeSignupPersonalInfoView,
    EmployeeSignupPhoneView,
    EmployeeSignupSubmitView,
    EmployeeSignupVerifyOTPView,
    EmployeeSignupWorkInfoView,
    HouseholdEmployerSignupView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    SkillListCreateView,
    UserProfileView,
)

urlpatterns = [
    path("skills", SkillListCreateView.as_view(), name="skills"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/profile", UserProfileView.as_view(), name="user-profile"),
    path("auth/password/forgot", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password/verify-otp", PasswordResetVerifyView.as_view(), name="password-reset-verify"),
    path("auth/password/reset", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("auth/employee/signup/phone", EmployeeSignupPhoneView.as_view(), name="employee-signup-phone"),
    path("auth/employee/signup/verify-otp", EmployeeSignupVerifyOTPView.as_view(), name="employee-signup-verify"),
    path("auth/employee/signup/personal", EmployeeSignupPersonalInfoView.as_view(), name="employee-signup-personal"),
    path("auth/employee/signup/work", EmployeeSignupWorkInfoView.as_view(), name="employee-signup-work"),
    path("auth/employee/signup/id-documents", EmployeeSignupIDDocumentsView.as_view(), name="employee-signup-id-documents"),
    path("auth/employee/signup/submit", EmployeeSignupSubmitView.as_view(), name="employee-signup-submit"),
    path("auth/employer/signup/household", HouseholdEmployerSignupView.as_view(), name="employer-signup-household"),
    path("auth/employer/signup/company", CompanyEmployerSignupView.as_view(), name="employer-signup-company"),
]
