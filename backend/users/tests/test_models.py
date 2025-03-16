from django.test import TestCase
from django.contrib.auth import get_user_model

# Create your tests here.


class ModelTests(TestCase):

    def test_create_user_with_email_ok(self):
        """Test creating a user with an email address works."""
        email = "testuser1@example.com"
        password = "testPwd1!"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_created_user_email_normalized(self):
        """Test email address of new users is normalized."""
        test_emails = [
            ["testuser1@EXAMPLE.com", "testuser1@example.com"],
            ["TestUser2@Example.com", "TestUser2@example.com"],
            ["TESTUSER3@EXAMPLE.com", "TESTUSER3@example.com"],
            ["testuser4@example.COM", "testuser4@example.com"],
        ]
        for email, expected in test_emails:
            user = get_user_model().objects.create_user(email, "testPwd1!")
            self.assertEqual(user.email, expected)

    def test_create_user_without_email_fails(self):
        """Test creating a user without an email address fails."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "testPwd1!")

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            "testadmin@example.com",
            "testPwd1!",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_user_with_duplicate_email_fails(self):
        """Test creating a user with a duplicate email fails."""
        email = "testuser@example.com"
        password = "testPwd1!"
        get_user_model().objects.create_user(email=email, password=password)
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(email=email, password=password)
