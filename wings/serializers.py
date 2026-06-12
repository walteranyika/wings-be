import re
from datetime import date

from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmployeeProfile, EmployeeSignupApplication, SignupOTP, Skill, User


KENYAN_COUNTIES = {
    "Baringo",
    "Bomet",
    "Bungoma",
    "Busia",
    "Elgeyo-Marakwet",
    "Embu",
    "Garissa",
    "Homa Bay",
    "Isiolo",
    "Kajiado",
    "Kakamega",
    "Kericho",
    "Kiambu",
    "Kilifi",
    "Kirinyaga",
    "Kisii",
    "Kisumu",
    "Kitui",
    "Kwale",
    "Laikipia",
    "Lamu",
    "Machakos",
    "Makueni",
    "Mandera",
    "Marsabit",
    "Meru",
    "Migori",
    "Mombasa",
    "Murang'a",
    "Nairobi",
    "Nakuru",
    "Nandi",
    "Narok",
    "Nyamira",
    "Nyandarua",
    "Nyeri",
    "Samburu",
    "Siaya",
    "Taita-Taveta",
    "Tana River",
    "Tharaka-Nithi",
    "Trans Nzoia",
    "Turkana",
    "Uasin Gishu",
    "Vihiga",
    "Wajir",
    "West Pokot",
}


def normalize_phone(value):
    phone = re.sub(r"[\s-]+", "", str(value or ""))
    if phone.startswith("07") or phone.startswith("01"):
        phone = f"+254{phone[1:]}"
    elif phone.startswith("254"):
        phone = f"+{phone}"

    if not re.fullmatch(r"\+254(7|1)\d{8}", phone):
        raise serializers.ValidationError(
            "Enter a valid Kenyan phone number, for example +254712345678."
        )
    return phone


def otp_for_phone(phone):
    digits = re.sub(r"\D", "", phone)
    return digits[-6:]


def validate_full_name(value):
    cleaned = " ".join(str(value or "").split())
    if len(cleaned.split()) < 2:
        raise serializers.ValidationError("Provide at least two names.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", cleaned):
        raise serializers.ValidationError("Full name can only contain letters, spaces, hyphens, and apostrophes.")
    return cleaned


def validate_age(value):
    today = timezone.localdate()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise serializers.ValidationError("Employee must be at least 18 years old.")
    if age > 50:
        raise serializers.ValidationError("Employee must not be older than 50 years.")
    return value


def validate_counties(values):
    values = values or []
    invalid = sorted(set(values) - KENYAN_COUNTIES)
    if invalid:
        raise serializers.ValidationError(
            f"Unknown Kenyan county/county names: {', '.join(invalid)}."
        )
    return values


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class EmployeeProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    id_front = serializers.SerializerMethodField()
    id_back = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = [
            "skills",
            "preferred_counties",
            "bio",
            "id_front",
            "id_back",
        ]

    def get_file_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(file_field.url)
        return file_field.url

    def get_id_front(self, obj):
        return self.get_file_url(obj.id_front)

    def get_id_back(self, obj):
        return self.get_file_url(obj.id_back)


class UserProfileSerializer(serializers.ModelSerializer):
    employee_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "full_name",
            "national_id",
            "date_of_birth",
            "gender",
            "user_type",
            "review_status",
            "employee_profile",
        ]

    def get_employee_profile(self, obj):
        if not hasattr(obj, "employee_profile"):
            return None
        return EmployeeProfileSerializer(
            obj.employee_profile,
            context=self.context,
        ).data


class EmployeeSignupPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        app = EmployeeSignupApplication.objects.filter(phone=phone).first()
        if app and app.status == EmployeeSignupApplication.Status.SUBMITTED:
            raise serializers.ValidationError("An application with this phone number is already under review.")
        return phone

    def save(self, **kwargs):
        phone = self.validated_data["phone"]
        application, _ = EmployeeSignupApplication.objects.update_or_create(
            phone=phone,
            defaults={"status": EmployeeSignupApplication.Status.OTP_PENDING},
        )
        SignupOTP.objects.create(
            phone=phone,
            purpose=SignupOTP.Purpose.EMPLOYEE_SIGNUP,
            otp=otp_for_phone(phone),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        return application


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)
    purpose = SignupOTP.Purpose.EMPLOYEE_SIGNUP

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate(self, attrs):
        otp = (
            SignupOTP.objects.filter(
                phone=attrs["phone"],
                purpose=self.purpose,
            )
            .order_by("-created_at")
            .first()
        )
        if not otp or otp.otp != attrs["otp"]:
            raise serializers.ValidationError({"otp": "Invalid OTP."})
        if otp.has_expired():
            raise serializers.ValidationError({"otp": "OTP has expired."})
        attrs["otp_record"] = otp
        return attrs

    def save(self, **kwargs):
        otp_record = self.validated_data["otp_record"]
        otp_record.is_verified = True
        otp_record.save(update_fields=["is_verified"])
        return otp_record


class EmployeeSignupOTPVerifySerializer(OTPVerifySerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not EmployeeSignupApplication.objects.filter(phone=attrs["phone"]).exists():
            raise serializers.ValidationError({"phone": "Start signup with this phone number first."})
        return attrs

    def save(self, **kwargs):
        super().save(**kwargs)
        application = EmployeeSignupApplication.objects.get(phone=self.validated_data["phone"])
        application.status = EmployeeSignupApplication.Status.OTP_VERIFIED
        application.save(update_fields=["status", "updated_at"])
        return application


class EmployeePersonalInfoSerializer(serializers.Serializer):
    phone = serializers.CharField()
    full_name = serializers.CharField(max_length=255)
    national_id = serializers.CharField(max_length=20)
    dob = serializers.DateField()
    gender = serializers.ChoiceField(choices=["Male", "Female", "male", "female"])
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate_full_name(self, value):
        return validate_full_name(value)

    def validate_national_id(self, value):
        national_id = str(value).strip()
        if not re.fullmatch(r"\d{6,10}", national_id):
            raise serializers.ValidationError("National ID must contain 6 to 10 digits.")
        if User.objects.filter(national_id=national_id).exists():
            raise serializers.ValidationError("An account with this national ID already exists.")
        qs = EmployeeSignupApplication.objects.filter(national_id=national_id).exclude(
            phone=normalize_phone(self.initial_data.get("phone"))
        )
        if qs.exists():
            raise serializers.ValidationError("An application with this national ID already exists.")
        return national_id

    def validate_dob(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return validate_age(value)

    def validate_gender(self, value):
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        password_validation.validate_password(attrs["password"])
        application = EmployeeSignupApplication.objects.filter(phone=attrs["phone"]).first()
        if not application or application.status == EmployeeSignupApplication.Status.OTP_PENDING:
            raise serializers.ValidationError({"phone": "Verify OTP before adding personal information."})
        attrs["application"] = application
        return attrs

    def save(self, **kwargs):
        application = self.validated_data["application"]
        application.full_name = self.validated_data["full_name"]
        application.national_id = self.validated_data["national_id"]
        application.date_of_birth = self.validated_data["dob"]
        application.gender = self.validated_data["gender"]
        application.password_hash = make_password(self.validated_data["password"])
        application.status = EmployeeSignupApplication.Status.PERSONAL_COMPLETE
        application.save()
        return application


class EmployeeWorkInfoSerializer(serializers.Serializer):
    phone = serializers.CharField()
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        allow_empty=False,
    )
    preferred_counties = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
    )
    description = serializers.CharField(min_length=20, max_length=1000)

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate_skills(self, value):
        cleaned = sorted({" ".join(skill.split()).title() for skill in value if skill.strip()})
        if not cleaned:
            raise serializers.ValidationError("Provide at least one skill.")
        return cleaned

    def validate_preferred_counties(self, value):
        return validate_counties(value)

    def validate(self, attrs):
        application = EmployeeSignupApplication.objects.filter(phone=attrs["phone"]).first()
        if not application or not application.password_hash:
            raise serializers.ValidationError({"phone": "Complete personal information first."})
        attrs["application"] = application
        return attrs

    def save(self, **kwargs):
        application = self.validated_data["application"]
        skill_objects = [
            Skill.objects.get_or_create(name=skill_name)[0]
            for skill_name in self.validated_data["skills"]
        ]
        application.skills.set(skill_objects)
        application.preferred_counties = self.validated_data.get("preferred_counties", [])
        application.bio = self.validated_data["description"]
        application.status = EmployeeSignupApplication.Status.WORK_COMPLETE
        application.save()
        return application


class EmployeeIDDocumentsSerializer(serializers.Serializer):
    phone = serializers.CharField()
    id_front = serializers.ImageField()
    id_back = serializers.ImageField()

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate(self, attrs):
        application = EmployeeSignupApplication.objects.filter(phone=attrs["phone"]).first()
        if not application or application.status not in [
            EmployeeSignupApplication.Status.WORK_COMPLETE,
            EmployeeSignupApplication.Status.DOCUMENTS_COMPLETE,
        ]:
            raise serializers.ValidationError({"phone": "Complete work information first."})
        attrs["application"] = application
        return attrs

    def save(self, **kwargs):
        application = self.validated_data["application"]
        application.id_front = self.validated_data["id_front"]
        application.id_back = self.validated_data["id_back"]
        application.status = EmployeeSignupApplication.Status.DOCUMENTS_COMPLETE
        application.save()
        return application


class EmployeeSubmitApplicationSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate(self, attrs):
        application = EmployeeSignupApplication.objects.filter(phone=attrs["phone"]).first()
        if not application:
            raise serializers.ValidationError({"phone": "No application found for this phone number."})
        if application.status == EmployeeSignupApplication.Status.SUBMITTED:
            raise serializers.ValidationError({"phone": "This application has already been submitted."})
        missing = []
        for field in ["full_name", "national_id", "date_of_birth", "gender", "password_hash", "bio", "id_front", "id_back"]:
            if not getattr(application, field):
                missing.append(field)
        if not application.skills.exists():
            missing.append("skills")
        if missing:
            raise serializers.ValidationError({"missing_fields": missing})
        if User.objects.filter(phone=application.phone).exists():
            raise serializers.ValidationError({"phone": "An account with this phone number already exists."})
        attrs["application"] = application
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        application = self.validated_data["application"]
        user = User.objects.create(
            phone=application.phone,
            full_name=application.full_name,
            national_id=application.national_id,
            date_of_birth=application.date_of_birth,
            gender=application.gender,
            user_type=User.UserType.EMPLOYEE,
            review_status=User.ReviewStatus.UNDER_REVIEW,
            is_active=True,
            password=application.password_hash,
        )
        profile = EmployeeProfile.objects.create(
            user=user,
            preferred_counties=application.preferred_counties,
            bio=application.bio,
            id_front=application.id_front,
            id_back=application.id_back,
        )
        profile.skills.set(application.skills.all())
        application.status = EmployeeSignupApplication.Status.SUBMITTED
        application.submitted_user = user
        application.save(update_fields=["status", "submitted_user", "updated_at"])
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            phone=attrs["phone"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")
        if user.review_status != User.ReviewStatus.APPROVED:
            raise serializers.ValidationError("Your application is still under review.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "phone": user.phone,
                "full_name": user.full_name,
                "user_type": user.user_type,
                "review_status": user.review_status,
            },
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if not User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("No account exists with this phone number.")
        return phone

    def save(self, **kwargs):
        phone = self.validated_data["phone"]
        SignupOTP.objects.create(
            phone=phone,
            purpose=SignupOTP.Purpose.PASSWORD_RESET,
            otp=otp_for_phone(phone),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        return phone


class PasswordResetVerifySerializer(OTPVerifySerializer):
    purpose = SignupOTP.Purpose.PASSWORD_RESET


class PasswordResetConfirmSerializer(PasswordResetVerifySerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        user = User.objects.get(phone=attrs["phone"])
        password_validation.validate_password(attrs["password"], user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        self.validated_data["otp_record"].is_verified = True
        self.validated_data["otp_record"].save(update_fields=["is_verified"])
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password", "updated_at"])
        return user
