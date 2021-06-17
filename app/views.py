import textwrap

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import BadHeaderError, EmailMessage
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView, View)

from .forms import CommentForm, ContactForm, TipForm
from .models import Code, Comment, Like, Notification, Tip


# tip作成者のみ処理可能
class OnlyMyTipMixin(UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        try:
            tip = Tip.objects.get(id = self.kwargs['pk'])
        except Tip.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                        {'verbose_name': Tip._meta.verbose_name})
        return tip.created_by == self.request.user


class IndexView(TemplateView):
    template_name = 'app/index.html'


class TipCreate(LoginRequiredMixin, CreateView):
    model = Tip
    form_class = TipForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # formのチェックでrequest.userを使用するため設定
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Tipを登録しました。')
        return resolve_url('app:tip_list')


class TipDetail(LoginRequiredMixin, DetailView):
    model = Tip
    
    def get_object(self):
        obj = super().get_object()
        # created_by!=request.user and private は表示不可
        if obj.created_by != self.request.user and obj.public_set == Tip.PRIVATE:
            raise PermissionDenied('そのページは非公開です。')
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # コメントformを設定
        # コメント入力エラー時はsessionにrequest.POSTが保存されているため、それを使用してコメントの内容を復元
        session_comment_form_data = self.request.session.pop('comment_form_data', None)
        context['form'] = CommentForm(session_comment_form_data)
        # お気に入り済み判定を設定
        context['is_liked'] = self.object.is_liked_by_user(self.request.user)
        # コメントとコードを設定
        comments = Comment.objects.filter(tip=self.object).select_related('created_by')
        context['comments'] = comments
        context['comments_distinct'] = comments.order_by('created_by_id').distinct().values('created_by_id', 'created_by__username')
        context['codes'] = Code.objects.filter(tip=self.object)
        return context

    def get_queryset(self):
        queryset = Tip.objects.all().annotate(like_count=Count("likes"))
        
        return queryset


class TipList(LoginRequiredMixin, ListView):
    model = Tip
    paginate_by = 12

    def get_queryset(self):
        path = self.request.path_info

        # My Tips と Public Tips で表示するTipを変更
        if 'tip_list' in path:
            queryset = Tip.objects.filter(
                Q(created_by=self.request.user) | Q(likes__created_by=self.request.user)
            ).annotate(like_count=Count("likes")).select_related('created_by').prefetch_related('tags')
        elif 'tip_public_list' in path:
            queryset = Tip.objects.filter(public_set=Tip.PUBLIC).annotate(like_count=Count("likes")).select_related('created_by').prefetch_related('tags')
        else:
            raise Http404("そのページは存在しません。")

        # 表示対象で抽出
        search_target = self.request.GET.get('searchTarget','')

        if search_target == 'my':
            queryset = queryset.filter(created_by=self.request.user)
        elif search_target == 'other':
            queryset = queryset.exclude(created_by=self.request.user)
        else:
            pass

        # 検索内容で抽出
        query = self.request.GET.get('query','')
        tagquery = self.request.GET.get('tagQuery','')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(codes__filename__icontains=query) | Q(codes__content__icontains=query)
            ).distinct()
        if tagquery:
            queryset = queryset.filter(tags__name__icontains=tagquery)

        # 表示順で並び替え
        display_order = self.request.GET.get('displayOrder','')

        if display_order == 'liked':
            queryset = queryset.annotate(num_likes=Count('likes')).order_by('-num_likes')
        else:
            queryset = queryset.order_by('-updated_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        path = self.request.path_info

        # My Tips と Public Tips で表示するtitleを変更
        if 'tip_list' in path:
            context['title'] = 'My Tips'
        elif 'tip_public_list' in path:
            context['title'] = 'Public Tips'
        else:
            raise Http404("そのページは存在しません。")

        return context


class TipUpdate(OnlyMyTipMixin, UpdateView):
    model = Tip
    form_class = TipForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # formのチェックでrequest.userを使用するため設定
        return kwargs

    def get_success_url(self):
        messages.info(self.request, 'Tipを更新しました。')
        return resolve_url('app:tip_detail', pk=self.kwargs['pk'])


class TipDelete(OnlyMyTipMixin, DeleteView):
    model = Tip

    def get_success_url(self):
        messages.info(self.request, 'Tipを削除しました。')
        return resolve_url('app:tip_list')


@login_required
def add_comment(request, pk):
    tip = get_object_or_404(Tip, pk=pk)
    if tip.public_set == Tip.PRIVATE:
            raise PermissionDenied('そのページにはコメントできません。')
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            to_users_id = request.POST.getlist('toUsersId',[])
            if to_users_id:
                if 'no' in to_users_id:
                    form.save_with_otherfields(request=request, tip=tip)
                else:
                    form.save_with_otherfields(request=request, tip=tip, to_users_id=to_users_id)

                messages.success(request, 'コメントを追加しました。')
                return redirect('app:tip_detail', pk=pk)
            else:
                # select文の宛先が選択されていないケース(通常ありえない)
                messages.error(request, 'コメントに宛先が指定されていません。')
        else:
            # TODO 現状form.is_validでのエラーは表示されない。フォームがコメント欄しかないので現状そこまで問題ない。
                # return renderにするとformは設定できるが、TipDetailで実施しているcommentやcodeをcontextに設定する必要がある。viewに書きすぎ？
                # sessionの設定をPickleSerializerにすればformをsessionに設定可能？(現状はnot JSON serializableでエラー)
            # formのエラーケース
            messages.error(request, 'コメントの作成に失敗しました。')
        
        # redirect先でコメントの入力内容を保持するため、sessionにPOSTを設定
        request.session['comment_form_data'] = request.POST
        return redirect('app:tip_detail', pk=pk)
        
    return redirect('app:tip_detail', pk=pk)


@login_required
def add_like(request, pk):
    tip = get_object_or_404(Tip, pk=pk)
    if tip.public_set == Tip.PRIVATE or tip.created_by == request.user:
            raise PermissionDenied('そのページをお気に入りに追加することはできません。')
    like = Like.objects.filter(created_by=request.user).filter(tip=tip)
    if like.exists():
        messages.info(request, 'すでにお気に入りに追加済みです。')
        return redirect('app:tip_detail', pk=pk)

    if Tip.objects.filter(created_by=request.user).count() < 2:
        messages.error(request, 'お気に入りへの追加は２つ以上のTip登録が必要です。')
        return redirect('app:tip_detail', pk=pk)

    like = Like(created_by=request.user, tip=tip)
    like.save()
    messages.success(request, 'お気に入りに追加しました。')
    return redirect('app:tip_detail', pk=pk)


@login_required
def delete_like(request, pk):
    tip = get_object_or_404(Tip, pk=pk)
    if tip.public_set == Tip.PRIVATE or tip.created_by == request.user:
            raise PermissionDenied('そのページからお気に入りを削除することはできません。')
    like = Like.objects.filter(created_by=request.user).filter(tip=tip)
    if not like.exists():
        messages.info(request, 'すでにお気に入りから削除済みです。')
        return redirect('app:tip_detail', pk=pk)

    like.first().delete()
    messages.success(request, 'お気に入りから削除しました。')
    return redirect('app:tip_detail', pk=pk)

class ContactView(View):
    def get(self, request, *args, **kwargs):
        form = ContactForm(request.POST or None)
        return render(request, 'app/contact.html', {
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST or None)

        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            subject = '[TipStock]お問い合わせありがとうございます。'
            contact = textwrap.dedent('''
                ※このメールはシステムからの自動返信です。

                {name} 様

                お問い合わせありがとうございました。
                以下の内容でお問い合わせを受付いたしました。
                内容を確認させていただき、ご返信させて頂きますので、少々お待ち下さい。

                -----------------------
                ■お名前
                {name}

                ■メールアドレス
                {email}

                ■メッセージ
                {message}
                -----------------------
                ''').format(
                    name=name,
                    email=email,
                    message=message,
                )
            to_list = [email]
            bcc_list = [settings.EMAIL_HOST_USER]

            try:
                message = EmailMessage(subject=subject, body=contact,to=to_list, bcc=bcc_list)
                message.send()
            except BadHeaderError:
                return HttpResponse('無効なヘッダが検出されました。')

            return redirect('app:thanks')

        return render(request, 'app/contact.html', {
            'form': form,
        })


class ThanksView(TemplateView):
    template_name = 'app/thanks.html'


@login_required
def notifications(request):
    goto = request.GET.get('goto', '')
    notification_id = request.GET.get('notification', 0)
    notifications = Notification.objects.filter(to_user=request.user).select_related('tip', 'created_by')

    # お知らせをクリック
    if goto != '':
        try:
            notification = notifications.get(pk=notification_id)
        except Notification.DoesNotExist:
            # url指定で自分以外のお知らせにアクセスしようとした場合
            raise PermissionDenied('そのお知らせへのアクセスは禁止されています。')

        if notification.is_read == False:
            notification.is_read = True
            notification.save()

        if notification.category == Notification.COMMENT:
            return redirect('app:tip_detail', pk=notification.tip.pk)
        elif notification.category == Notification.EVENT:
            return redirect('app:tip_detail', pk=notification.tip.pk)

        # TODO 今後機能を追加した場合追加
        # elif notification.category == Notification.MESSAGE:
        #     return redirect('app:message', username=notification.created_by.username)
        # elif notification.category == Notification.FOLLOW:
        #     return redirect('app:follow', username=notification.to_user.username)

    # 全て既読をクリック
    all_read = request.GET.get('allRead', '')

    if all_read == 'done':
        update_notifications = []
        for notification in notifications:
            if notification.is_read == False:
                notification.is_read = True
                update_notifications.append(notification)
        Notification.objects.bulk_update(update_notifications, fields=['is_read'])

    # 全てをクリック
    display = request.GET.get('display', '')

    if display != 'all':
        notifications = notifications.filter(is_read=False)

    return render(request, 'app/notifications.html', {
        'notifications': notifications
    })
