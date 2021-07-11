import os
from datetime import datetime

from accounts.tests.factories import UserFactory
from app.models import Code, Comment, Like, Notification, Tip
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from .factories import (CodeFactory, CommentFactory, LikeFactory,
                        NotificationFactory, TipFactory)


class TestTip(TestCase):

    def test_is_empty(self):
        """初期状態チェック"""
        tips = Tip.objects.all()
        self.assertEqual(tips.count(), 0)

    def test_is_count_one(self):
        """1レコード作成し、レコードが1つだけカウントされること"""
        TipFactory()
        tips = Tip.objects.all()
        self.assertEqual(tips.count(), 1)

    def test_input_and_default_values(self):
        """入力値、default値とDB値が一致すること"""
        
        now = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        with freeze_time(now):
            title = 'タイトル'
            description = '説明'
            tags = ['tag1', 'tag2']
            tweet = 'ツイート'
            create_username = 'user1'
            created_by = UserFactory(username=create_username)
            public_set = 'private'

            TipFactory(
                title=title,
                description=description,
                tags=tags,
                tweet=tweet,
                created_by=created_by,
                public_set=public_set,
            )

        tips = Tip.objects.all()
        actual_tip = tips[0]
        
        self.assertEqual(actual_tip.title, title)
        self.assertEqual(actual_tip.description, description)
        set_tags = set()
        for tag in actual_tip.tags.all():
            set_tags.add(tag.name)
        self.assertSetEqual(set_tags, set(tags))
        self.assertEqual(actual_tip.tweet, tweet)
        self.assertEqual(actual_tip.created_by, created_by)
        self.assertEqual(actual_tip.created_by.username, create_username)
        self.assertEqual(actual_tip.created_at, now)
        self.assertEqual(actual_tip.updated_at, now)
        self.assertEqual(actual_tip.public_set, public_set)
        
    def test_is_liked_by_user(self):
        tip_created_by = UserFactory()
        tip = TipFactory(created_by=tip_created_by)
        like_created_by = UserFactory()
        
        # お気に入り登録前
        self.assertFalse(tip.is_liked_by_user(like_created_by))
        
        # お気に入り登録後
        like = LikeFactory(tip=tip, created_by=like_created_by)
        self.assertTrue(tip.is_liked_by_user(like_created_by))



class TestCode(TestCase):

    def test_is_empty(self):
        """初期状態チェック"""
        codes = Code.objects.all()
        self.assertEqual(codes.count(), 0)

    def test_is_count_one(self):
        """1レコード作成し、レコードが1つだけカウントされること"""
        CodeFactory()
        codes = Code.objects.all()
        self.assertEqual(codes.count(), 1)

    def test_input_and_default_values(self):
        """入力値、default値とDB値が一致すること"""
        
        title = 'タイトル'
        tip = TipFactory(title=title)
        filename = 'file1.py'
        content = 'a = 3'

        CodeFactory(
            tip=tip,
            filename=filename,
            content=content,
        )

        codes = Code.objects.all()
        actual_code = codes[0]
        
        self.assertEqual(actual_code.tip, tip)
        self.assertEqual(actual_code.tip.title, title)
        self.assertEqual(actual_code.filename, filename)
        self.assertEqual(actual_code.content, content)


class TestComment(TestCase):

    def test_is_empty(self):
        """初期状態チェック"""
        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 0)

    def test_is_count_one(self):
        """1レコード作成し、レコードが1つだけカウントされること"""
        CommentFactory()
        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 1)

    def test_input_and_default_values(self):
        """入力値、default値とDB値が一致すること"""
        
        now = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        with freeze_time(now):
            title = 'タイトル'
            tip = TipFactory(title=title)
            no = 1
            to_users_name = ['user1', 'user2']
            to_users = [UserFactory(username=to_user_name) for to_user_name in to_users_name]
            text = 'コメント'
            create_username = 'user3'
            created_by = UserFactory(username=create_username)

            CommentFactory(
                tip=tip,
                no=no,
                to_users=to_users,
                text=text,
                created_by=created_by,
            )

        comments = Comment.objects.all()
        actual_comment = comments[0]
        
        self.assertEqual(actual_comment.tip, tip)
        self.assertEqual(actual_comment.tip.title, title)
        self.assertEqual(actual_comment.no, no)
        set_to_users = set()
        for to_user in actual_comment.to_users.all():
            set_to_users.add(to_user.username)
        self.assertSetEqual(set_to_users, set(to_users_name))
        self.assertEqual(actual_comment.text, text)
        self.assertEqual(actual_comment.text, text)
        self.assertEqual(actual_comment.text, text)
        self.assertEqual(actual_comment.created_by, created_by)
        self.assertEqual(actual_comment.created_by.username, create_username)
        self.assertEqual(actual_comment.created_at, now)


class LikeComment(TestCase):

    def test_is_empty(self):
        """初期状態チェック"""
        likes = Like.objects.all()
        self.assertEqual(likes.count(), 0)

    def test_is_count_one(self):
        """1レコード作成し、レコードが1つだけカウントされること"""
        LikeFactory()
        likes = Like.objects.all()
        self.assertEqual(likes.count(), 1)

    def test_input_and_default_values(self):
        """入力値、default値とDB値が一致すること"""
        
        now = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        with freeze_time(now):
            title = 'タイトル'
            tip = TipFactory(title=title)
            create_username = 'user1'
            created_by = UserFactory(username=create_username)

            LikeFactory(
                tip=tip,
                created_by=created_by,
            )

        likes = Like.objects.all()
        actual_like = likes[0]
        
        self.assertEqual(actual_like.tip, tip)
        self.assertEqual(actual_like.tip.title, title)
        self.assertEqual(actual_like.created_by, created_by)
        self.assertEqual(actual_like.created_by.username, create_username)
        self.assertEqual(actual_like.created_at, now)


class TestNotification(TestCase):

    def test_is_empty(self):
        """初期状態チェック"""
        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 0)

    def test_is_count_one(self):
        """1レコード作成し、レコードが1つだけカウントされること"""
        NotificationFactory()
        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 1)

    def test_input_and_default_values(self):
        """入力値、default値とDB値が一致すること"""
        
        now = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        with freeze_time(now):
            to_user_name = 'user1'
            to_user = UserFactory(username=to_user_name)
            category = 'comment'
            title = 'タイトル'
            tip = TipFactory(title=title)
            content = 'お知らせ'
            create_username = 'user2'
            created_by = UserFactory(username=create_username)

            NotificationFactory(
                to_user=to_user,
                category=category,
                tip=tip,
                content=content,
                created_by=created_by,
            )

        notifications = Notification.objects.all()
        actual_notification = notifications[0]
        
        self.assertEqual(actual_notification.to_user, to_user)
        self.assertEqual(actual_notification.to_user.username, to_user_name)
        self.assertEqual(actual_notification.category, category)
        self.assertEqual(actual_notification.tip, tip)
        self.assertEqual(actual_notification.tip.title, title)
        self.assertEqual(actual_notification.content, content)
        self.assertEqual(actual_notification.is_read, False)
        self.assertEqual(actual_notification.created_by, created_by)
        self.assertEqual(actual_notification.created_by.username, create_username)
        self.assertEqual(actual_notification.created_at, now)

