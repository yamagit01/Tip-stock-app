import textwrap

from allauth.account import views
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from allauth.account.utils import (filter_users_by_email,
                                   send_email_confirmation)
from app.models import Notification, Tip
from app.utils import create_notification
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import BadHeaderError, EmailMessage
from django.dispatch import receiver
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from accounts.forms import ProfileForm, ReRegistrationForm, WithdrawalForm
from accounts.models import User


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        tips = Tip.objects.filter(created_by=user_data)
        private_tips_count = tips.filter(public_set=Tip.PRIVATE).count()
        public_tips_count = tips.filter(public_set=Tip.PUBLIC).count()

        return render(request, 'accounts/profile.html', {
            'user_data': user_data,
            'private_tips_count': private_tips_count,
            'public_tips_count': public_tips_count,
        })
        
        
class YourProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.pk == self.kwargs.get('pk'):
            return redirect('accounts:profile')
        user_data = get_object_or_404(User, pk=self.kwargs.get('pk'))
        tips = Tip.objects.filter(created_by=user_data)
        public_tips_count = tips.filter(public_set=Tip.PUBLIC).count()
        
        return render(request, 'accounts/your_profile.html', {
            'user_data': user_data,
            'public_tips_count': public_tips_count,
        })
        

class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        form = ProfileForm(
            request.POST or None,
            initial = {
                'username': user_data.username,
                'icon': user_data.icon,
                'self_introduction': user_data.self_introduction
            }
        )
        
        return render(request, 'accounts/profile_edit.html', {
            'form': form,
        })
        
    def post(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        form = ProfileForm(request.POST or None, request.FILES or None, instance=user_data)

        if form.is_valid():
            user_data.username = form.cleaned_data.get('username')
            user_data.self_introduction = form.cleaned_data.get('self_introduction')
            if request.FILES:
                user_data.icon = request.FILES.get('icon')
            user_data.save()
            return redirect('accounts:profile')

        return render(request, 'accounts/profile_edit.html', {
            'form': form,
        })


class LoginView(views.LoginView):
    template_name = 'accounts/login.html'


@login_required
def logout_view(request):
    logout(request)
    return redirect('app:index')
    

class SignupView(views.SignupView):
    template_name = 'accounts/signup.html'


class PasswordChangeView(LoginRequiredMixin, views.PasswordChangeView):
    success_url = reverse_lazy('accounts:profile')


class PasswordSetView(LoginRequiredMixin, views.PasswordSetView):
    success_url = reverse_lazy('accounts:profile')


class WithdrawalView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = WithdrawalForm(request.POST or None)
        
        return render(request, 'accounts/withdrawal.html', {
            'form': form,
        })
        
    def post(self, request, *args, **kwargs):
        user_data = User.objects.get(id=request.user.id)
        form = WithdrawalForm(request.POST)

        if form.is_valid():
            private_tip_has_left = form.cleaned_data.get('private_tip_has_left')
            # 退会ユーザのデータ削除
            if not private_tip_has_left:
                # privatetipを全て削除
                Tip.objects.filter(created_by=user_data, public_set=Tip.PRIVATE).delete()
            # notificationを全削除
            Notification.objects.filter(to_user=user_data).delete()
            # emailaddressを削除
            EmailAddress.objects.filter(user=user_data).delete()
            # userのiconをNone、is_activateをfalseに更新
            user_data.icon = None
            user_data.is_active = False
            user_data.save()
            # 退会メールを送信
            name = user_data.username
            email = user_data.email
            subject = '[TipStock]退会手続き完了のお知らせ'
            contact = textwrap.dedent(f'''
                ※このメールはシステムからの自動返信です。

                {name} 様

                退会手続きを完了いたしました。
                この度はTipStockをご利用いただき誠にありがとうございました。
                本ユーザアカウントで再登録をご希望の場合は、
                サイト内のユーザ登録から「退会ユーザの再登録」を実施ください。
                
                TipStock
                https://www.tipstock.info/
                [お問い合わせページ]
                https://www.tipstock.info/contact/
                ''')
            to_list = [email]
            bcc_list = [settings.BCC_EMAIL]

            try:
                message = EmailMessage(subject=subject, body=contact,to=to_list, bcc=bcc_list)
                message.send()
            except BadHeaderError:
                # TODO この時点でログアウトしており、loginページredirectになる？
                return HttpResponse('無効なヘッダが検出されました。')

            # 退会完了ページに移動
            return redirect('accounts:withdrawal_done')

        return render(request, 'accounts/withdrawal.html', {
            'form': form,
        })


class WithdrawalDoneView(TemplateView):
    template_name = 'accounts/withdrawal_done.html'


class ReRegistrationView(View):
    def get(self, request, *args, **kwargs):
        form = ReRegistrationForm(request.POST or None)
        
        return render(request, 'accounts/reregistration.html', {
            'form': form,
        })
        
    def post(self, request, *args, **kwargs):
        form = ReRegistrationForm(request.POST or None)

        if form.is_valid():
            email = form.cleaned_data.get('email')
            # 入力したemailでuserのis_activeがfalseのuser(再登録対象者)を抽出
            user = filter_users_by_email(email, is_active=False)
            if user:
                # HACK verifyの判定のためemailaddressを取得しているが、
                    # send_email_confirmation内でも同じ処理でverifyの判定をしている（ただ、returnがないので判別はできない）。
                    # 自前で同様の関数を作成すれば2度読みは解消できるが、とりあえずは実行数も少ないので既存の関数をそのまま使用。
                try:
                    emailaddress = EmailAddress.objects.get_for_user(user[0], email)
                    # 通常userのis_activeはfalseでemailaddressのverifiedがtrueというケースはありえないが
                    # もしそのような状態になっている場合はverifiedをfalseにして再度メール認証を行い、userをactiveにする。
                    # (send_email_confirmation内でverifiedがTrueの場合は処理しないため)
                    if emailaddress.verified == True:
                        emailaddress.verified = False
                        emailaddress.save()
                except EmailAddress.DoesNotExist:
                    pass
                
                send_email_confirmation(request, user[0], email=email)
                adapter = get_adapter(request)
                return adapter.respond_email_verification_sent(request, user)

            form.add_error('email', '未登録、または有効なユーザのメールアドレスです。')
            return render(request, 'accounts/reregistration.html', {
                'form': form,
            })

        return render(request, 'accounts/reregistration.html', {
            'form': form,
        })


@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    user = email_address.user
    if user.is_active == False:
        user.is_active = True
        user.save()


@login_required
def follow_user(request, pk):
    user = request.user
    if user.pk == pk:
        raise PermissionDenied('自身へのフォローはできません。')
    followed_user = get_object_or_404(User, pk=pk)
    follows = user.follows.all()
    #既にフォローしていればメッセージのみ送信
    if followed_user in follows:
        messages.info(request, 'フォロー済みです。')
    else:
        user.follows.add(followed_user)
        messages.success(request, 'フォローしました')
        create_notification(request, to_user=followed_user, category=Notification.FOLLOW)

    return redirect('accounts:your_profile', pk=pk)


@login_required
def unfollow_user(request, pk):
    user = request.user
    if user.pk == pk:
        raise PermissionDenied('自身へのフォロー解除はできません。')
    followed_user = get_object_or_404(User, pk=pk)
    follows = user.follows.all()
    #既にフォロー解除済みであればメッセージのみ送信
    if followed_user in follows:
        user.follows.remove(followed_user)
        messages.success(request, 'フォローを解除しました')
    else:
        messages.info(request, 'フォロー解除済みです。')

    return redirect('accounts:your_profile', pk=pk)


def follows(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    path = request.path_info
    if 'follows' in path:
        # フォローを表示
        follows = user.follows.all().prefetch_related('created_tip')
        title = 'フォロー'
    else:
        # フォロワーを表示
        follows = user.followed_by.all().prefetch_related('created_tip')
        title = 'フォロワー'

    latest_tip = []
    public_tips_counts = []
    for user in follows:
        tips = Tip.objects.filter(public_set=Tip.PUBLIC, created_by=user).order_by('-updated_at')
        if tips.exists():
            latest_tip.append(tips.first())
            public_tips_counts.append(tips.count())
        else:
            latest_tip.append('')
            public_tips_counts.append(0)

    return render(request, 'accounts/follow.html', {
        'follows': follows,
        'latest_tip': latest_tip,
        'public_tips_counts': public_tips_counts,
        'title': title,
    })
