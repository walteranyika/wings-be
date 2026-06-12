from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Skill
from .serializers import (
    CompanyEmployerSignupSerializer,
    EmployeeIDDocumentsSerializer,
    EmployeePersonalInfoSerializer,
    EmployeeSignupOTPVerifySerializer,
    EmployeeSignupPhoneSerializer,
    EmployeeSubmitApplicationSerializer,
    EmployeeWorkInfoSerializer,
    HouseholdEmployerSignupSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    SkillSerializer,
    token_response_for_user,
    UserProfileSerializer,
)


class SkillListCreateView(generics.ListCreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class EmployeeSignupPhoneView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmployeeSignupPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "OTP generated successfully.",
                "otp_hint": "Use the last 6 digits of the phone number while SMS is pending.",
            },
            status=status.HTTP_201_CREATED,
        )


class EmployeeSignupVerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmployeeSignupOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Phone number verified successfully."})


class EmployeeSignupPersonalInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmployeePersonalInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Personal information saved successfully."})


class EmployeeSignupWorkInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmployeeWorkInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Work preferences saved successfully."})


class EmployeeSignupIDDocumentsView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = EmployeeIDDocumentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "ID documents uploaded successfully."})


class EmployeeSignupSubmitView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmployeeSubmitApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Your application has been submitted and is under review."},
            status=status.HTTP_201_CREATED,
        )


class HouseholdEmployerSignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = HouseholdEmployerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Household employer account created successfully.",
                **token_response_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


class CompanyEmployerSignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CompanyEmployerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Company employer account created successfully.",
                **token_response_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save())


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Password reset OTP generated successfully.",
                "otp_hint": "Use the last 6 digits of the phone number while SMS is pending.",
            }
        )


class PasswordResetVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password reset OTP verified successfully."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password reset successfully."})
