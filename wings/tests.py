from rest_framework import status
from rest_framework.test import APITestCase

from .models import EmployerProfile, User


class EmployerSignupTests(APITestCase):
    def test_household_employer_signup_creates_approved_employer_account(self):
        response = self.client.post(
            "/api/auth/employer/signup/household",
            {
                "full_name": "Jane Employer",
                "email": "jane@example.com",
                "phone": "0712345601",
                "location": "Nairobi",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(phone="+254712345601")
        self.assertEqual(user.full_name, "Jane Employer")
        self.assertEqual(user.user_type, User.UserType.EMPLOYER)
        self.assertEqual(user.review_status, User.ReviewStatus.APPROVED)
        self.assertTrue(user.check_password("StrongPass123!"))

        profile = user.employer_profile
        self.assertEqual(profile.employer_type, EmployerProfile.EmployerType.HOUSEHOLD)
        self.assertEqual(profile.email, "jane@example.com")
        self.assertEqual(profile.location, "Nairobi")
        self.assertEqual(profile.company_name, "")
        self.assertIsNone(profile.company_registration_number)

    def test_company_employer_signup_creates_company_profile(self):
        response = self.client.post(
            "/api/auth/employer/signup/company",
            {
                "company_name": "Acme Services Ltd",
                "email": "hello@acme.example",
                "phone": "0712345602",
                "location": "Mombasa",
                "company_registration_number": "cp-12345",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(phone="+254712345602")
        self.assertEqual(user.full_name, "Acme Services Ltd")
        self.assertEqual(user.user_type, User.UserType.EMPLOYER)
        self.assertEqual(user.review_status, User.ReviewStatus.APPROVED)

        profile = user.employer_profile
        self.assertEqual(profile.employer_type, EmployerProfile.EmployerType.COMPANY)
        self.assertEqual(profile.email, "hello@acme.example")
        self.assertEqual(profile.location, "Mombasa")
        self.assertEqual(profile.company_name, "Acme Services Ltd")
        self.assertEqual(profile.company_registration_number, "CP-12345")
