import os
import unittest
import urllib
from unittest import mock

from accounts.tests.factories import UserFactory
from allauth.account.models import EmailAddress
from app.models import Notification, Tip
from app.tests.factories import NotificationFactory, TipFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import BadHeaderError
from django.test import Client, TestCase
from django.urls import reverse

UserModel = get_user_model()


class TestProfileView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url =reverse('accounts:profile')

    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)
        
    def test_get_request(self):
        """getリクエストの正常確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        user = response.context['user_data']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertEqual(user, self.user)


class TestProfileEditView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url =reverse('accounts:profile_edit')

    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_edit.html')

    def test_form_field(self):
        """form表示の確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        form = response.context['form']
        
        self.assertIn('username', form.fields)
        self.assertIn('icon', form.fields)
        self.assertEqual(form.initial['username'], self.user.username)
        self.assertEqual(form.initial['icon'], self.user.icon)

    def test_post_request(self):
        """postリクエストの正常確認(form更新)"""
        
        self.client.force_login(self.user)
        form_username = 'usernameA'
        form_icon = 'icon_test.png'
        with open(f'./accounts/tests/{form_icon}', 'rb') as fp:
            form_data = {
                'username': form_username,
                'icon': fp,
            }
            response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, reverse('accounts:profile'), status_code=302, target_status_code=200)
        
        user = UserModel.objects.get(pk=self.user.pk)

        self.assertEqual(user.username, form_username)
        self.assertEqual(os.path.basename(user.icon.name)[37:], form_icon)


class TestLoginView(unittest.TestCase):

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        client = Client()
        response = client.get(reverse('accounts:login'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['accounts/login.html'])


class TestLoginView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url =reverse('accounts:logout')
        
    def test_get_request(self):
        """getリクエストの正常確認"""
        
        self.client.force_login(self.user)
        self.assertIn('_auth_user_id', self.client.session)  # ログイン状態
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse('app:index'), status_code=302, target_status_code=200)
        self.assertNotIn('_auth_user_id', self.client.session)  # ログアウト状態


class TestSignupView(unittest.TestCase):

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        client = Client()
        response = client.get(reverse('accounts:signup'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['accounts/signup.html'])


class TestWithdrawalView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.public_tip = TipFactory(created_by=cls.user, public_set='public')
        cls.private_tip = TipFactory(created_by=cls.user, public_set='private')
        cls.notification = NotificationFactory(to_user=cls.user)
        cls.emailaddress = EmailAddress.objects.create(email=cls.user.email, verified=True, primary=True, user=cls.user)
        cls.url =reverse('accounts:withdrawal')

    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/withdrawal.html')

    def test_form_field(self):
        """form表示の確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        form = response.context['form']
        
        self.assertIn('private_tip_has_left', form.fields)

    def test_post_request_with_private_tip_has_left(self):
        """postリクエストの正常確認(private_tip_has_left=True)"""
        
        self.client.force_login(self.user)
        form_data = {
            'private_tip_has_left': True,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('accounts:withdrawal_done'), status_code=302, target_status_code=200)
        
        user = UserModel.objects.get(pk=self.user.pk)

        self.assertTrue(Tip.objects.filter(pk=self.public_tip.pk).exists())
        self.assertTrue(Tip.objects.filter(pk=self.private_tip.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=self.notification.pk).exists())
        self.assertFalse(EmailAddress.objects.filter(pk=self.emailaddress.pk).exists())
        self.assertFalse(user.icon)
        self.assertFalse(user.is_active)
        
    def test_post_request_with_private_tip_has_not_left(self):
        """postリクエストの正常確認(private_tip_has_left=False)"""
        
        self.client.force_login(self.user)
        form_data = {
            'private_tip_has_left': False,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('accounts:withdrawal_done'), status_code=302, target_status_code=200)
        
        user = UserModel.objects.get(pk=self.user.pk)

        self.assertTrue(Tip.objects.filter(pk=self.public_tip.pk).exists())
        self.assertFalse(Tip.objects.filter(pk=self.private_tip.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=self.notification.pk).exists())
        self.assertFalse(EmailAddress.objects.filter(pk=self.emailaddress.pk).exists())
        self.assertFalse(user.icon)
        self.assertFalse(user.is_active)


    def test_post_request_send_email(self):
        """postリクエストの正常確認(email)"""
        
        self.client.force_login(self.user)
        form_data = {
            'private_tip_has_left': False,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('accounts:withdrawal_done'), status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[TipStock]退会手続き完了のお知らせ')
        self.assertIn(self.user.username, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].bcc, [settings.EMAIL_HOST_USER])

    @mock.patch("accounts.views.EmailMessage.send")
    def test_post_request_send_email(self, send_mail_mock):
        """postリクエストのBadHeaderError確認"""
        
        send_mail_mock.side_effect = BadHeaderError()
        form_data = {
            'private_tip_has_left': False,
        }
        response = self.client.get(self.url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)


class TestWithdrawalDoneView(unittest.TestCase):

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        client = Client()
        response = client.get(reverse('accounts:withdrawal_done'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['accounts/withdrawal_done.html'])


class TestReRegistrationView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_active=False)
        cls.url =reverse('accounts:reregistration')

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/reregistration.html')

    def test_form_field(self):
        """form表示の確認"""
        
        response = self.client.get(self.url)
        form = response.context['form']
        
        self.assertIn('email', form.fields)

    def test_post_request_with_no_emailaddress(self):
        """postリクエストの正常確認(ia_active=False, emailaddressなし)"""
        
        form_data = {
            'email': self.user.email,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('account_email_verification_sent'), status_code=302, target_status_code=200)
        emailaddress = EmailAddress.objects.filter(email=self.user.email)
        self.assertEqual(emailaddress.count(), 1)
        self.assertFalse(emailaddress[0].verified)
        self.assertEqual(len(mail.outbox), 1)
        
    def test_post_request_with_emailaddress_verified_false(self):
        """postリクエストの正常確認(ia_active=False, emailaddressあり(verified=False))"""
        
        emailaddress = EmailAddress.objects.create(email=self.user.email, verified=False, primary=True, user=self.user)
        form_data = {
            'email': self.user.email,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('account_email_verification_sent'), status_code=302, target_status_code=200)
        emailaddress = EmailAddress.objects.filter(email=self.user.email)
        self.assertEqual(emailaddress.count(), 1)
        self.assertFalse(emailaddress[0].verified)
        self.assertEqual(len(mail.outbox), 1)
        
    def test_post_request_with_emailaddress_verified_true(self):
        """postリクエストの正常確認(ia_active=False, emailaddressあり(verified=True))"""
        
        emailaddress = EmailAddress.objects.create(email=self.user.email, verified=True, primary=True, user=self.user)
        form_data = {
            'email': self.user.email,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('account_email_verification_sent'), status_code=302, target_status_code=200)
        emailaddress = EmailAddress.objects.filter(email=self.user.email)
        self.assertEqual(emailaddress.count(), 1)
        self.assertFalse(emailaddress[0].verified)
        self.assertEqual(len(mail.outbox), 1)
        
    def test_post_request_with_user_is_active_true(self):
        """postリクエストの正常確認(ia_active=True, emailaddressなし)"""
        
        self.user.is_active=True
        self.user.save()
        form_data = {
            'email': self.user.email,
        }
        response = self.client.post(self.url, form_data, follow=True)
        form = response.context['form']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/reregistration.html')
        self.assertEqual(form['email'].errors, ['未登録、または有効なユーザのメールアドレスです。'])
        emailaddress = EmailAddress.objects.filter(email=self.user.email)
        self.assertEqual(emailaddress.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        
    def test_post_request_with_no_user(self):
        """postリクエストの正常確認(ユーザなし, emailaddressなし)"""
        
        no_user_email = f'abc{self.user.email}'
        form_data = {
            'email': no_user_email,
        }
        response = self.client.post(self.url, form_data, follow=True)
        form = response.context['form']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/reregistration.html')
        self.assertEqual(form['email'].errors, ['未登録、または有効なユーザのメールアドレスです。'])
        emailaddress = EmailAddress.objects.filter(email=no_user_email)
        self.assertEqual(emailaddress.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
