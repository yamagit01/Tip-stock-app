from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from .factories import UserFactory

UserModel = get_user_model()

class TestUserModel(TestCase):

    def test_is_empty(self):
        """初期状態チェック"""
        users = UserModel.objects.all()
        self.assertEqual(users.count(), 0)

    def test_is_count_one(self):
        """1レコード作成し、レコードが1つだけカウントされること"""
        user = UserFactory()
        users = UserModel.objects.all()
        self.assertEqual(users.count(), 1)

    def test_input_and_default_values(self):
        """入力値、default値とDB値が一致すること"""
        
        now = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        with freeze_time(now):
            username = 'user1'
            email = 'user1@example.com'
            password = 'password'
            icon__filename = 'user1.png'

            UserFactory(
                username=username,
                email=email,
                password=password,
                icon__filename=icon__filename,
            )

        users = UserModel.objects.all()
        actual_user = users[0]
        
        self.assertEqual(actual_user.username, username)
        self.assertEqual(actual_user.email, email)
        self.assertNotEqual(actual_user.password, password)
        self.assertIsNotNone(actual_user.icon)
        self.assertEqual(actual_user.is_active, True)
        self.assertEqual(actual_user.is_staff, False)
        self.assertEqual(actual_user.is_superuser, False)
        self.assertEqual(actual_user.date_joined, now)
