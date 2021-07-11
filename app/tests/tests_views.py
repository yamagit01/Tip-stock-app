import os
import unittest
import urllib
from datetime import datetime
from unittest import mock

from accounts.tests.factories import UserFactory
from app.models import Code, Comment, Like, Notification, Tip
from app.tests.factories import (CodeFactory, CommentFactory, LikeFactory,
                                 NotificationFactory, TipFactory)
from django.conf import settings
from django.core import mail
from django.core.mail import BadHeaderError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time


class TestIndexView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url =reverse('app:index')
        
    def test_get_request_by_anonymous_user(self):
        """getリクエストの正常確認（未ログインユーザ）"""
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['app/index.html'])
        self.assertContains(response, 'ホーム</a>')
        self.assertContains(response, 'Public Tips</a>')
        self.assertContains(response, 'ユーザ登録</a>')
        self.assertContains(response, 'ログイン</a>')
        self.assertContains(response, 'お問い合わせ</a>')
        self.assertNotContains(response, 'Tip Form</a>')
        self.assertNotContains(response, 'My Tips</a>')
        self.assertNotContains(response, 'お知らせ (0)</a>')
        self.assertNotContains(response, 'プロフィール</a>')
        self.assertNotContains(response, 'ログアウト</a>')

    def test_get_request_by_login_user(self):
        """getリクエストの正常確認（ログインユーザ）"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['app/index.html'])
        self.assertContains(response, 'ホーム</a>')
        self.assertContains(response, 'Public Tips</a>')
        self.assertNotContains(response, 'ユーザ登録</a>')
        self.assertNotContains(response, 'ログイン</a>')
        self.assertContains(response, 'お問い合わせ</a>')
        self.assertContains(response, 'Tip Form</a>')
        self.assertContains(response, 'My Tips</a>')
        self.assertContains(response, 'お知らせ (0)</a>')
        self.assertContains(response, 'プロフィール</a>')
        self.assertContains(response, 'ログアウト</a>')


class TestTipCreateView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url =reverse('app:tip_create')
        
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
        self.assertTemplateUsed(response, 'app/tip_form.html')
        
    def test_form_field(self):
        """form表示の確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        form = response.context_data['form']
        
        self.assertIn('title', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('tags', form.fields)
        self.assertIn('tweet', form.fields)
        self.assertIn('public_set', form.fields)
        self.assertIn('filename', form.formset[0].fields)
        self.assertIn('content', form.formset[0].fields)
        
    def test_post_request(self):
        """postリクエストの正常確認"""
        
        self.client.force_login(self.user)
        form_title = 'タイトル'
        form_description = '説明'
        form_tags = 'tag1,tag2'
        form_tweet = 'ツイート'
        form_public_set = 'private'
        form_filename = 'filename.py'
        form_content = 'a = 3'
        now = timezone.make_aware(datetime(2021, 3, 4, 15, 57, 11, 703055))
        with freeze_time(now):
            form_data = {
                'title': form_title,
                'description': form_description,
                'tags': form_tags,
                'tweet': form_tweet,
                'public_set': form_public_set,
                'codes-TOTAL_FORMS': 1,
                'codes-INITIAL_FORMS': 0,
                'codes-MIN_NUM_FORMS': 1,
                'codes-MAX_NUM_FORMS': 5,
                'codes-0-filename': form_filename,
                'codes-0-content': form_content,
            }
            response = self.client.post(self.url, form_data, follow=True)
                
        
        self.assertRedirects(response, reverse('app:tip_list'), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Tipを登録しました。')
        
        tips = Tip.objects.all()
        self.assertEqual(tips.count(), 1)
        tip = tips.first()
        code = Code.objects.get(tip=tip)

        self.assertEqual(tip.title, form_title)
        self.assertEqual(tip.description, form_description)
        self.assertCountEqual([tag.name for tag in tip.tags.all()], list(set(form_tags.split(','))))
        self.assertEqual(tip.tweet, form_tweet)
        self.assertEqual(tip.public_set, form_public_set)
        self.assertEqual(tip.updated_at, now)
        self.assertEqual(tip.created_at, now)
        self.assertEqual(tip.created_by, self.user)
        self.assertEqual(code.filename, form_filename)
        self.assertEqual(code.content, form_content)


class TestTipDetailView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.create_user = UserFactory()
        cls.non_create_user = UserFactory()
        cls.private_tip = TipFactory(created_by=cls.create_user, public_set='private')
        cls.public_tip = TipFactory(created_by=cls.create_user, public_set='public', tags=['tag1', 'tag2'])
        cls.public_tip_no_comment_and_like = TipFactory(created_by=cls.create_user, public_set='public')
        cls.code = CodeFactory(tip=cls.public_tip)
        cls.comment = CommentFactory(tip=cls.public_tip, to_users=[cls.create_user], created_by=cls.non_create_user)
        cls.like = LikeFactory(tip=cls.public_tip, created_by=cls.non_create_user)
        cls.private_tip_url =reverse('app:tip_detail', args=[cls.private_tip.pk])
        cls.public_tip_url =reverse('app:tip_detail', args=[cls.public_tip.pk])
        cls.public_tip2_url =reverse('app:tip_detail', args=[cls.public_tip_no_comment_and_like.pk])

    def test_get_request_to_private_tip_by_anonymous_user(self):
        """getリクエスト/未ログインユーザ/PrivateTip/403エラー"""
        
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_public_tip_by_anonymous_user(self):
        """getリクエスト/未ログインユーザ/PublicTip/正常"""
        
        response = self.client.get(self.public_tip_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_detail.html')

    def test_get_request_to_private_tip_by_cerate_user(self):
        """getリクエスト/Tip作成者/PrivateTip/正常"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_detail.html')
        
    def test_get_request_to_public_tip_by_cerate_user(self):
        """getリクエスト/Tip作成者/PublicTip/正常"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_detail.html')
        
    def test_get_request_to_private_tip_by_non_create_user(self):
        """getリクエスト/Tip作成者以外/PrivateTip/403エラー"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_public_tip_by_non_create_user(self):
        """getリクエスト/Tip作成者以外/PublicTip/正常"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_detail.html')
        
    def test_tip_context(self):
        """tipのcontext確認"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url)
        tip = response.context_data['tip']
        
        self.assertEqual(tip.title, self.public_tip.title)
        self.assertEqual(tip.description, self.public_tip.description)
        self.assertQuerysetEqual(tip.tags.all(), self.public_tip.tags.all(), ordered=False)
        self.assertEqual(tip.tweet, self.public_tip.tweet)
        self.assertEqual(tip.public_set, self.public_tip.public_set)
        self.assertEqual(tip.updated_at, self.public_tip.updated_at)
        self.assertEqual(tip.created_at, self.public_tip.created_at)
        self.assertEqual(tip.created_by, self.public_tip.created_by)
        
    def test_code_context(self):
        """codeのcontext確認"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url)
        codes = response.context_data['codes']
        
        self.assertEqual(codes.count(), 1)
        self.assertEqual(codes[0].filename, self.code.filename)
        self.assertEqual(codes[0].content, self.code.content)

    def test_comment_context(self):
        """commentのcontext確認"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url)
        form = response.context_data['form']
        comments = response.context_data['comments']
        comments_distinct = response.context_data['comments_distinct']
        
        self.assertIn('text', form.fields)
        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments[0].no, self.comment.no)
        self.assertEqual(comments[0].text, self.comment.text)
        self.assertEqual(comments[0].to_users, self.comment.to_users)
        self.assertEqual(comments[0].created_by, self.comment.created_by)
        self.assertEqual(comments[0].created_at, self.comment.created_at)
        self.assertEqual(comments_distinct.count(), 1)
        self.assertEqual(comments_distinct[0].get('created_by__username'), self.comment.created_by.username)
        
    def test_like_context(self):
        """likeのcontext確認"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url)
        is_liked = response.context_data['is_liked']
        tip = response.context_data['tip']

        self.assertTrue(is_liked)
        self.assertEqual(tip.like_count, 1)

    def test_display_public_tip_with_no_comment_and_like_to_non_create_user(self):

        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip2_url)
        
        self.assertContains(response, 'まだコメントはありません')
        self.assertContains(response, 'コメント投稿')
        self.assertContains(response, '</i>&nbsp;0</span>')
        self.assertContains(response, 'お気に入り登録')
        
    def test_display_public_tip_with_comment_and_like_to_non_create_user(self):

        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertContains(response, self.comment.text)
        self.assertContains(response, 'コメント投稿')
        self.assertNotContains(response, 'なし(コメントがない場合はこの選択のみ)')
        self.assertContains(response, '登録者:')
        self.assertContains(response, '</i>&nbsp;1</span>')
        self.assertContains(response, 'お気に入り解除')
        self.assertNotContains(response, '更新</a>')
        self.assertNotContains(response, 'id="tip-delete-button">削除</button>')
        
    def test_display_public_tip_with_comment_and_like_to_create_user(self):

        self.client.force_login(self.create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertContains(response, self.comment.text)
        self.assertContains(response, 'コメント投稿')
        self.assertContains(response, 'なし(コメントがない場合はこの選択のみ)')
        self.assertNotContains(response, '登録者:')
        self.assertContains(response, '</i>&nbsp;1</span>')
        self.assertNotContains(response, 'お気に入り解除')
        self.assertNotContains(response, 'お気に入り登録')
        self.assertContains(response, '更新</a>')
        self.assertContains(response, 'id="tip-delete-button">削除</button>')
        
    def test_display_private_tip(self):

        self.client.force_login(self.create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertNotContains(response, 'まだコメントはありません')
        self.assertNotContains(response, 'コメント投稿')
        self.assertNotContains(response, '</i>&nbsp;0</span>')
        self.assertNotContains(response, 'お気に入り解除')
        self.assertNotContains(response, 'お気に入り登録')
        self.assertContains(response, '更新</a>')
        self.assertContains(response, 'id="tip-delete-button">削除</button>')

    def test_display_public_tip_with_no_comment_and_like_to_anonymous_user(self):

        response = self.client.get(self.public_tip2_url)
        
        self.assertContains(response, 'まだコメントはありません')
        self.assertNotContains(response, 'コメント投稿')
        self.assertContains(response, '</i>&nbsp;0</span>')
        self.assertNotContains(response, 'お気に入り解除')
        self.assertNotContains(response, 'お気に入り登録')
        self.assertNotContains(response, '更新</a>')
        self.assertNotContains(response, 'id="tip-delete-button">削除</button>')
        
    def test_display_public_tip_with_comment_and_like_to_anonymous_user(self):

        response = self.client.get(self.public_tip_url)
        
        self.assertContains(response, self.comment.text)
        self.assertNotContains(response, 'コメント投稿')
        self.assertNotContains(response, 'なし(コメントがない場合はこの選択のみ)')
        self.assertNotContains(response, '登録者:')
        self.assertContains(response, '</i>&nbsp;1</span>')
        self.assertNotContains(response, 'お気に入り解除')
        self.assertNotContains(response, 'お気に入り登録')
        self.assertNotContains(response, '更新</a>')
        self.assertNotContains(response, 'id="tip-delete-button">削除</button>')
        
        

class TestTipListView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory()
        cls.user2 = UserFactory()
        cls.tip_list_url =reverse('app:tip_list')
        cls.tip_public_list_url =reverse('app:tip_public_list')

    def test_get_request_to_private_tip_by_anonymous_user(self):
        """getリクエスト/未ログインユーザ/tip_list/ログインページにリダイレクト"""
        
        response = self.client.get(self.tip_list_url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.tip_list_url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)
        
    def test_get_request_to_public_tip_by_anonymous_user(self):
        """getリクエスト/未ログインユーザ/tip_public_list/正常"""
        
        response = self.client.get(self.tip_public_list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        
    def test_get_request_to_tip_list(self):
        """getリクエスト(tip_list)の正常確認"""
        
        user1_private_tip = TipFactory(created_by=self.user1, public_set='private')
        user1_public_tip = TipFactory(created_by=self.user1, public_set='public')
        user2_private_tip = TipFactory(created_by=self.user2, public_set='private')
        user2_public_tip = TipFactory(created_by=self.user2, public_set='public')
        like_user2_public_tip_by_user1 = LikeFactory(tip=user2_public_tip, created_by=self.user1)

        # user1(お気に入りあり)
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_list_url)
        tip_list_user1 = response.context_data['tip_list']

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_user1), [user1_private_tip, user1_public_tip, user2_public_tip])
        self.assertContains(response, 'My Tips')

        # user2(お気に入りなし)
        self.client.force_login(self.user2)
        response = self.client.get(self.tip_list_url)
        tip_list_user2 = response.context_data['tip_list']

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_user2), [user2_private_tip, user2_public_tip])


    def test_get_request_to_tip_public_list(self):
        """getリクエスト(tip_public_list)の正常確認"""
        
        user1_private_tip = TipFactory(created_by=self.user1, public_set='private')
        user1_public_tip = TipFactory(created_by=self.user1, public_set='public')
        user2_private_tip = TipFactory(created_by=self.user2, public_set='private')
        user2_public_tip = TipFactory(created_by=self.user2, public_set='public')
        like_user2_public_tip_by_user1 = LikeFactory(tip=user2_public_tip, created_by=self.user1)

        # user1(お気に入りあり)
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_public_list_url)
        tip_public_list_user1 = response.context_data['tip_list']

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_public_list_user1), [user1_public_tip, user2_public_tip])
        self.assertContains(response, 'Public Tips')

        # user2(お気に入りなし)
        self.client.force_login(self.user2)
        response = self.client.get(self.tip_public_list_url)
        tip_public_list_user2 = response.context_data['tip_list']

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_public_list_user2), [user1_public_tip, user2_public_tip])


    def test_get_request_with_query(self):
        """getリクエストのquery確認"""
        
        public_tip1 = TipFactory(title='aaa1', description='bbb1', created_by=self.user1, public_set='public')
        code1 = CodeFactory(tip=public_tip1, filename='ccc1', content='ddd1')
        public_tip2 = TipFactory(title='aaa2', description='bbb2', created_by=self.user1, public_set='public')
        code2 = CodeFactory(tip=public_tip2, filename='ccc2', content='ddd2')
        public_tip3 = TipFactory(title='aaa3', description='bbb3', created_by=self.user1, public_set='public')
        code3 = CodeFactory(tip=public_tip3, filename='ccc3', content='ddd3')
        public_tip4 = TipFactory(title='aaa4', description='aaa4', created_by=self.user1, public_set='public')
        code4 = CodeFactory(tip=public_tip4, filename='aaa4', content='aaa4')

        # 初期表示
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_public_list_url)
        tip_list = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list), [public_tip1, public_tip2, public_tip3, public_tip4])
        
        # title,複数該当、重複チェック
        response = self.client.get(self.tip_public_list_url, {'query': 'aaa'})
        tip_list_aaa = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_aaa), [public_tip1, public_tip2, public_tip3, public_tip4])
        
        # descriptionチェック
        response = self.client.get(self.tip_public_list_url, {'query': 'bbb1'})
        tip_list_bbb1 = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_bbb1), [public_tip1])

        # filenameチェック
        response = self.client.get(self.tip_public_list_url, {'query': 'ccc2'})
        tip_list_ccc2 = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_ccc2), [public_tip2])

        # contentチェック
        response = self.client.get(self.tip_public_list_url, {'query': 'ddd3'})
        tip_list_ddd3 = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_ddd3), [public_tip3])

        # 該当なしチェック
        response = self.client.get(self.tip_public_list_url, {'query': 'aaaa'})
        tip_list_aaaa = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertFalse(tip_list_aaaa.exists())
        self.assertContains(response, '投稿がありません')


    def test_get_request_with_tagquery(self):
        """getリクエストのtagQuery確認"""
        
        public_tip1 = TipFactory(tags=['tag1', 'tag2'], created_by=self.user1, public_set='public')
        public_tip2 = TipFactory(tags=['tag2', 'tag3'], created_by=self.user1, public_set='public')
        public_tip3 = TipFactory(tags=['tag'], created_by=self.user1, public_set='public')

        # 初期表示
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_public_list_url)
        tip_list = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list), [public_tip1, public_tip2, public_tip3])
        
        # 複数該当チェック
        response = self.client.get(self.tip_public_list_url, {'tagQuery': 'tag'})
        tip_list_tag = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_tag), [public_tip1, public_tip2, public_tip3])
        
        # １件チェック
        response = self.client.get(self.tip_public_list_url, {'tagQuery': 'tag1'})
        tip_list_tag1 = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_tag1), [public_tip1])

        # 該当なしチェック
        response = self.client.get(self.tip_public_list_url, {'tagQuery': 'tag4'})
        tip_list_tag4 = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertFalse(tip_list_tag4.exists())
        self.assertContains(response, '投稿がありません')
        
    def test_get_request_with_display_order(self):
        """getリクエストのdisplayOrder確認"""
        
        updated_at1 = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        updated_at2 = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703056))
        updated_at3 = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703057))
        
        public_tip1 = TipFactory(created_by=self.user1, updated_at=updated_at1, public_set='public')
        public_tip2 = TipFactory(created_by=self.user1, updated_at=updated_at2, public_set='public')
        public_tip3 = TipFactory(created_by=self.user1, updated_at=updated_at3, public_set='public')
        LikeFactory.create_batch(2, tip=public_tip1)
        LikeFactory(tip=public_tip2)

        # 初期表示(更新年月日順)
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_public_list_url)
        tip_list = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertListEqual(list(tip_list), [public_tip3, public_tip2, public_tip1])
        
        # 更新年月日順
        response = self.client.get(self.tip_public_list_url, {'displayOrder': 'updated'})
        tip_list_updated = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertListEqual(list(tip_list_updated), [public_tip3, public_tip2, public_tip1])

        # お気に入り数順
        response = self.client.get(self.tip_public_list_url, {'displayOrder': 'liked'})
        tip_list_liked = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertListEqual(list(tip_list_liked), [public_tip1, public_tip2, public_tip3])

    def test_get_request_with_search_target(self):
        """getリクエストのsearchTarget確認"""
        
        user1_public_tip1 = TipFactory(created_by=self.user1, public_set='public')
        user1_public_tip2 = TipFactory(created_by=self.user1, public_set='public')
        user2_public_tip1 = TipFactory(created_by=self.user2, public_set='public')

        # 初期表示
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_public_list_url)
        tip_list = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list), [user1_public_tip1, user1_public_tip2, user2_public_tip1])
        
        # 全体
        response = self.client.get(self.tip_public_list_url, {'searchTarget': 'all'})
        tip_list_all = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_all), [user1_public_tip1, user1_public_tip2, user2_public_tip1])
        
        # 自分のTips
        response = self.client.get(self.tip_public_list_url, {'searchTarget': 'my'})
        tip_list_my = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_my), [user1_public_tip1, user1_public_tip2])

        # 自分以外のTips
        response = self.client.get(self.tip_public_list_url, {'searchTarget': 'other'})
        tip_list_other = response.context_data['tip_list']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_list.html')
        self.assertCountEqual(list(tip_list_other), [user2_public_tip1])


    def test_get_request_with_pagination(self):
        """getリクエストのpagination確認"""
        
        from app.views import TipMyListView
        
        TipFactory.create_batch(TipMyListView.paginate_by, created_by=self.user1)
        
        self.client.force_login(self.user1)
        response = self.client.get(self.tip_list_url)
        page_obj = response.context_data['page_obj']
        
        self.assertEqual(page_obj.paginator.num_pages, 1)
        self.assertFalse(page_obj.has_next())
        
        TipFactory(created_by=self.user1)
        
        response = self.client.get(self.tip_list_url)
        page_obj = response.context_data['page_obj']
        
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())


class TestTipUpdateView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.create_user = UserFactory()
        cls.non_create_user = UserFactory()
        cls.created_at = timezone.make_aware(datetime(2021, 3, 4, 14, 57, 11, 703055))
        with freeze_time(cls.created_at):
            cls.tip = TipFactory(created_by=cls.create_user, public_set='public',tags=['tag1', 'tag2'])
        cls.code = CodeFactory(tip=cls.tip)
        cls.url =reverse('app:tip_update', args=[cls.tip.pk])
        
    def test_user_must_be_logged_in(self):
        """未ログインユーザは403エラー"""
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
                
    def test_get_request_by_create_user(self):
        """getリクエスト/Tip作成者/正常"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/tip_form.html')
        
    def test_get_request_by_non_create_user(self):
        """getリクエスト/Tip作成者以外/403エラー"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_tip_form(self):
        """form確認"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.url)
        form = response.context_data['form']
        
        self.assertEqual(form['title'].value(), self.tip.title)
        self.assertEqual(form['description'].value(), self.tip.description)
        self.assertQuerysetEqual(form['tags'].value(), self.tip.tags.all(), ordered=False)
        self.assertEqual(form['tweet'].value(), self.tip.tweet)
        self.assertEqual(form['public_set'].value(), self.tip.public_set)
        self.assertEqual(len(form.formset), 1)
        self.assertEqual(form.formset[0]['filename'].value(), self.code.filename)
        self.assertEqual(form.formset[0]['content'].value(), self.code.content)

    def test_post_request(self):
        """postリクエストの正常確認(form(code含む)更新)"""
        
        self.client.force_login(self.create_user)
        form_title = 'タイトル'
        form_description = '説明'
        form_tags = 'tag1,tag2'
        form_tweet = 'ツイート'
        form_public_set = 'private'
        form_code1 = ['filename.py', 'a = 3']
        form_code2 = ['filename.js', 'b = 5']
        now = timezone.make_aware(datetime(2021, 3, 4, 15, 57, 11, 703055))
        with freeze_time(now):
            form_data = {
                'title': form_title,
                'description': form_description,
                'tags': form_tags,
                'tweet': form_tweet,
                'public_set': form_public_set,
                'codes-TOTAL_FORMS': 3,
                'codes-INITIAL_FORMS': 1,
                'codes-MIN_NUM_FORMS': 1,
                'codes-MAX_NUM_FORMS': 5,
                'codes-0-id': self.code.id,
                'codes-0-filename': '',
                'codes-0-content': '',
                'codes-0-DELETE': 'on',
                'codes-1-filename': form_code1[0],
                'codes-1-content': form_code1[1],
                'codes-2-filename': form_code2[0],
                'codes-2-content': form_code2[1],
            }
            response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Tipを更新しました。')
        
        tip = Tip.objects.get(pk=self.tip.pk)
        codes = Code.objects.filter(tip=tip)

        self.assertEqual(tip.title, form_title)
        self.assertEqual(tip.description, form_description)
        self.assertCountEqual([tag.name for tag in tip.tags.all()], list(set(form_tags.split(','))))
        self.assertEqual(tip.tweet, form_tweet)
        self.assertEqual(tip.public_set, form_public_set)
        self.assertEqual(tip.updated_at, now)
        self.assertEqual(tip.created_at, self.created_at)
        self.assertEqual(tip.created_by, self.create_user)
        self.assertListEqual([[code.filename, code.content] for code in codes], [form_code1, form_code2])


class TestTipDeleteView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.create_user = UserFactory()
        cls.non_create_user = UserFactory()
        cls.tip = TipFactory(created_by=cls.create_user, public_set='public',tags=['tag1', 'tag2'])
        cls.code = CodeFactory(tip=cls.tip)
        cls.comment = CommentFactory(tip=cls.tip)
        cls.like = LikeFactory(tip=cls.tip)
        cls.notification = NotificationFactory(tip=cls.tip)
        cls.url =reverse('app:tip_delete', args=[cls.tip.pk])
        
    def test_user_must_be_logged_in(self):
        """未ログインユーザは403エラー"""
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_by_create_user(self):
        """getリクエスト/Tip作成者/リダイレクト"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.url)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.tip.pk]), status_code=302, target_status_code=200)
        
    def test_get_request_by_non_create_user(self):
        """getリクエスト/Tip作成者以外/403エラー"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_post_request_by_create_user(self):
        """postリクエスト/Tip作成者/正常"""
        
        self.client.force_login(self.create_user)
        response = self.client.post(self.url, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_list'), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Tipを削除しました。')
        
        self.assertFalse(Tip.objects.filter(pk=self.tip.pk).exists())
        self.assertFalse(Code.objects.filter(tip=self.tip).exists())
        self.assertFalse(Comment.objects.filter(tip=self.tip).exists())
        self.assertFalse(Like.objects.filter(tip=self.tip).exists())
        self.assertFalse(Notification.objects.filter(tip=self.tip).exists())
        
        
    def test_post_request_by_non_create_user(self):
        """postリクエスト/Tip作成者以外/403エラー"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')


class TestAddComment(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.create_user = UserFactory()
        cls.non_create_user = UserFactory()
        cls.private_tip = TipFactory(created_by=cls.create_user, public_set='private')
        cls.public_tip = TipFactory(created_by=cls.create_user, public_set='public')
        cls.private_tip_url =reverse('app:add_comment', args=[cls.private_tip.pk])
        cls.public_tip_url =reverse('app:add_comment', args=[cls.public_tip.pk])
        cls.no_tip_url =reverse('app:add_comment', args=['10'])
        
    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.public_tip_url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.public_tip_url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)
        
    def test_get_request_to_no_page(self):
        """Tipのないpkでアクセスは404エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.no_tip_url)
        
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        
    def test_get_request_to_public_tip(self):
        """getリクエスト/public_tip/正常(処理されず再表示)"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('app/tip_detail.html')
        
    def test_post_request_to_private_tip(self):
        """postリクエスト/private_tip/403エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.post(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_post_request_to_public_tip_by_create_user(self):
        """postリクエスト/public_tip/Tip作成者/正常"""
        
        self.client.force_login(self.create_user)
        now = timezone.make_aware(datetime(2021, 3, 4, 15, 57, 11, 703055))
        form_text = 'コメント'
        with freeze_time(now):
            form_data = {
                'text': form_text,
                'toUsersId': 'no',
            }

            response = self.client.post(self.public_tip_url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'コメントを追加しました。')
        
        comments = Comment.objects.filter(tip=self.public_tip)
        notifications = Notification.objects.filter(tip=self.public_tip)

        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments[0].no, 1)
        self.assertFalse(comments[0].to_users.exists())
        self.assertEqual(comments[0].text, form_text)
        self.assertEqual(comments[0].created_by, self.create_user)
        self.assertEqual(comments[0].created_at, now)
        self.assertFalse(notifications.exists())
        
    def test_post_request_to_public_tip_by_non_create_user(self):
        """postリクエスト/public_tip/Tip作成者以外/正常"""
        
        self.client.force_login(self.non_create_user)
        now = timezone.make_aware(datetime(2021, 3, 4, 15, 57, 11, 703055))
        form_text = 'コメント'
        with freeze_time(now):
            form_data = {
                'text': form_text,
                'toUsersId': self.create_user.pk,
            }

            response = self.client.post(self.public_tip_url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'コメントを追加しました。')
        
        comments = Comment.objects.filter(tip=self.public_tip)
        notifications = Notification.objects.filter(tip=self.public_tip)

        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments[0].no, 1)
        self.assertEqual(comments[0].to_users.all()[0], self.create_user)
        self.assertEqual(comments[0].text, form_text)
        self.assertEqual(comments[0].created_by, self.non_create_user)
        self.assertEqual(comments[0].created_at, now)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications[0].to_user, self.create_user)
        self.assertEqual(notifications[0].category, Notification.COMMENT)
        self.assertEqual(notifications[0].content, '')
        self.assertFalse(notifications[0].is_read)
        self.assertEqual(notifications[0].to_user, self.create_user)
        self.assertEqual(notifications[0].created_by, self.non_create_user)
        self.assertEqual(notifications[0].created_at, now)

    def test_post_request_error_about_to_user(self):
        """postリクエスト/public_tip/Tip作成者/宛先なしエラー(通常起きない)"""
        
        self.client.force_login(self.create_user)
        form_text = 'コメント'
        form_data = {
            'text': form_text,
        }
        response = self.client.post(self.public_tip_url, form_data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('app/tip_detail.html')
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'コメントに宛先が指定されていません。')
        
        comments = Comment.objects.filter(tip=self.public_tip)
        notifications = Notification.objects.filter(tip=self.public_tip)

        self.assertFalse(comments.exists())
        self.assertFalse(notifications.exists())
        
        form = response.context['form']
        self.assertEqual(form['text'].value(), form_text)
        
    def test_post_request_error_about_form(self):
        """postリクエスト/public_tip/Tip作成者/formエラー"""
        
        self.client.force_login(self.create_user)
        form_text = 'ばか'
        form_data = {
            'text': form_text,
            'toUsersId': 'no',
        }

        response = self.client.post(self.public_tip_url, form_data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('app/tip_detail.html')
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'コメントの作成に失敗しました。')
        
        comments = Comment.objects.filter(tip=self.public_tip)
        notifications = Notification.objects.filter(tip=self.public_tip)

        self.assertFalse(comments.exists())
        self.assertFalse(notifications.exists())
        
        form = response.context['form']
        self.assertEqual(form['text'].value(), form_text)
        self.assertEqual(form['text'].errors, ['コメントに暴言を含めないでください。'])


class TestAddLike(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.create_user = UserFactory()
        cls.non_create_user = UserFactory()
        cls.private_tip = TipFactory(created_by=cls.create_user, public_set='private')
        cls.public_tip = TipFactory(created_by=cls.create_user, public_set='public')
        cls.private_tip_url =reverse('app:add_like', args=[cls.private_tip.pk])
        cls.public_tip_url =reverse('app:add_like', args=[cls.public_tip.pk])
        cls.no_tip_url =reverse('app:add_like', args=['10'])
        
    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.public_tip_url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.public_tip_url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)
        
    def test_get_request_to_no_page(self):
        """Tipのないpkでアクセスは404エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.no_tip_url)
        
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        
    def test_get_request_to_private_tip_by_crate_user(self):
        """getリクエスト/private_tip/Tip作成者/403エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_public_tip_by_crate_user(self):
        """getリクエスト/public_tip/Tip作成者/403エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_private_tip_by_non_crate_user(self):
        """getリクエスト/private_tip/Tip作成者以外/403エラー"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_public_tip_by_non_crate_user(self):
        """getリクエスト/public_tip/Tip作成者以外(Tip2つ登録済み)/正常"""
        
        TipFactory.create_batch(2, created_by=self.non_create_user)
        
        self.client.force_login(self.non_create_user)
        now = timezone.make_aware(datetime(2021, 3, 4, 15, 57, 11, 703055))
        with freeze_time(now):
            response = self.client.get(self.public_tip_url, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'お気に入りに追加しました。')
        likes = Like.objects.filter(tip=self.public_tip, created_by=self.non_create_user)
        self.assertEqual(likes.count(), 1)
        self.assertEqual(likes[0].created_at, now)
        
    def test_get_request_to_public_tip_by_non_crate_user_added_like_error(self):
        """getリクエスト/public_tip/Tip作成者以外(Tip2つ登録済み)/既に登録済みでエラー"""
        
        TipFactory.create_batch(2, created_by=self.non_create_user)
        LikeFactory(tip=self.public_tip, created_by=self.non_create_user)
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'すでにお気に入りに追加済みです。')
        likes = Like.objects.filter(tip=self.public_tip, created_by=self.non_create_user)
        self.assertEqual(likes.count(), 1)

    def test_get_request_to_public_tip_by_non_crate_user_not_enough_tip_error(self):
        """getリクエスト/public_tip/Tip作成者以外/Tip1つのみ登録でエラー"""
        
        TipFactory(created_by=self.non_create_user)
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'お気に入りへの追加は２つ以上のTip登録が必要です。')
        likes = Like.objects.filter(tip=self.public_tip, created_by=self.non_create_user)
        self.assertEqual(likes.count(), 0)

class TestDeleteLike(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.create_user = UserFactory()
        cls.non_create_user = UserFactory()
        cls.private_tip = TipFactory(created_by=cls.create_user, public_set='private')
        cls.public_tip = TipFactory(created_by=cls.create_user, public_set='public')
        cls.private_tip_url =reverse('app:delete_like', args=[cls.private_tip.pk])
        cls.public_tip_url =reverse('app:delete_like', args=[cls.public_tip.pk])
        cls.no_tip_url =reverse('app:delete_like', args=['10'])
        LikeFactory(tip=cls.public_tip, created_by=cls.non_create_user)
        
    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.public_tip_url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.public_tip_url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)
        
    def test_get_request_to_no_page(self):
        """Tipのないpkでアクセスは404エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.no_tip_url)
        
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        
    def test_get_request_to_private_tip_by_crate_user(self):
        """getリクエスト/private_tip/Tip作成者/403エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_public_tip_by_crate_user(self):
        """getリクエスト/public_tip/Tip作成者/403エラー"""
        
        self.client.force_login(self.create_user)
        response = self.client.get(self.public_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_private_tip_by_non_crate_user(self):
        """getリクエスト/private_tip/Tip作成者以外/403エラー"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.private_tip_url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        
    def test_get_request_to_public_tip_by_non_crate_user(self):
        """getリクエスト/public_tip/Tip作成者以外/正常"""
        
        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'お気に入りから削除しました。')
        likes = Like.objects.filter(tip=self.public_tip, created_by=self.non_create_user)
        self.assertEqual(likes.count(), 0)
        
    def test_get_request_to_public_tip_by_non_crate_user_deleted_like_error(self):
        """getリクエスト/public_tip/Tip作成者以外/既に削除済みでエラー"""
        
        Like.objects.filter(tip=self.public_tip, created_by=self.non_create_user).delete()

        self.client.force_login(self.non_create_user)
        response = self.client.get(self.public_tip_url, follow=True)
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.public_tip.pk]), status_code=302, target_status_code=200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'すでにお気に入りから削除済みです。')
        likes = Like.objects.filter(tip=self.public_tip, created_by=self.non_create_user)
        self.assertEqual(likes.count(), 0)


class TestContactView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.url =reverse('app:contact')

    def test_get_request(self):
        """getリクエストの正常確認"""
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/contact.html')
        
    def test_form_field(self):
        """form表示の確認"""
        
        response = self.client.get(self.url)
        form = response.context['form']
        
        self.assertIn('name', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('message', form.fields)
        
    def test_post_request(self):
        """postリクエストの正常確認"""
        
        form_name = 'user'
        form_email = 'user@example.com'
        form_message = 'メッセージ'
        form_data = {
            'name': form_name,
            'email': form_email,
            'message': form_message,
        }
        response = self.client.post(self.url, form_data, follow=True)
        
        self.assertRedirects(response, reverse('app:thanks'), status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[TipStock]お問い合わせありがとうございます。')
        self.assertIn(form_name, mail.outbox[0].body)
        self.assertIn(form_email, mail.outbox[0].body)
        self.assertIn(form_message, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [form_email])
        self.assertEqual(mail.outbox[0].bcc, [settings.BCC_EMAIL])

    @mock.patch("app.views.EmailMessage.send")
    def test_post_request(self, send_mail_mock):
        """postリクエストのBadHeaderError確認"""
        
        send_mail_mock.side_effect = BadHeaderError()
        form_name = 'user'
        form_email = 'user@example.com'
        form_message = 'メッセージ'
        form_data = {
            'name': form_name,
            'email': form_email,
            'message': form_message,
        }
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), '無効なヘッダが検出されました。')


class TestThanksView(unittest.TestCase):
        
    def test_get_request(self):
        """getリクエストの正常確認"""
        
        client = Client()
        response = client.get(reverse('app:thanks'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ['app/thanks.html'])


class TestNotification(TestCase):
        
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.tip = TipFactory(created_by=cls.user, public_set='public')
        cls.comment_notification = NotificationFactory(to_user=cls.user, tip=cls.tip, category=Notification.COMMENT)
        cls.event_notification = NotificationFactory(to_user=cls.user, tip=cls.tip, category=Notification.EVENT)
        cls.url =reverse('app:notifications')

    def test_user_must_be_logged_in(self):
        """未ログインユーザはログインページにリダイレクト"""
        
        response = self.client.get(self.url, follow=True)
        expected_url = settings.LOGIN_URL + "?next=" + urllib.parse.quote(self.url, "")
        
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    def test_get_request(self):
        """getリクエストの正常確認(初期表示)"""

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        notifications = response.context['notifications']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/notifications.html')
        self.assertCountEqual(list(notifications), [self.comment_notification, self.event_notification])

    def test_get_request_with_display(self):
        """getリクエストのdisplay確認"""
        
        self.comment_notification.is_read = True
        self.comment_notification.save()

        # 初期表示
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        notifications = response.context['notifications']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/notifications.html')
        self.assertCountEqual(list(notifications), [self.event_notification])
        
        # 未確認のみ(unread)
        response = self.client.get(self.url, {'display': 'unread'})
        notifications = response.context['notifications']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/notifications.html')
        self.assertCountEqual(list(notifications), [self.event_notification])
        
        # 全て(all)
        response = self.client.get(self.url, {'display': 'all'})
        notifications = response.context['notifications']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/notifications.html')
        self.assertCountEqual(list(notifications), [self.comment_notification, self.event_notification])
        
    def test_get_request_with_allread(self):
        """getリクエストのallRead確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'allRead': 'done'})
        notifications = response.context['notifications']
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/notifications.html')
        self.assertFalse(notifications.exists())
        self.assertContains(response, '新しいお知らせはありません。')
        self.assertFalse(Notification.objects.filter(is_read=False).exists())

    def test_get_request_with_goto_comment(self):
        """getリクエストのgoto(comment)確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'goto': 'comment', 'notification': self.comment_notification.pk})
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.tip.pk]), status_code=302, target_status_code=200)
        self.assertTrue(Notification.objects.get(pk=self.comment_notification.pk).is_read)

    def test_get_request_with_goto_event(self):
        """getリクエストのgoto(event)確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'goto': 'event', 'notification': self.event_notification.pk})
        
        self.assertRedirects(response, reverse('app:tip_detail', args=[self.tip.pk]), status_code=302, target_status_code=200)
        self.assertTrue(Notification.objects.get(pk=self.event_notification.pk).is_read)

    def test_get_request_other_notification_access_error(self):
        """getリクエストの自分以外のお知らせアクセス403エラー確認"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'goto': 'comment', 'notification': '10'})
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

