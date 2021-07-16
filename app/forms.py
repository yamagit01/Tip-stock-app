from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.forms.models import inlineformset_factory

from .models import Code, Comment, Notification, Tip
from .utils import create_notification


class ModelFormWithFormSetMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formset = self.formset_class(
            instance=self.instance,
            data=self.data if self.is_bound else None,
        )

    def is_valid(self):
        return super().is_valid() and self.formset.is_valid()

    def save(self, commit=True):
        saved_instance = super().save(commit)
        self.formset.save(commit)
        return saved_instance


class CodeForm(forms.ModelForm):
    class Meta:
        model = Code
        fields = ('filename', 'content')


CodeFormSet = inlineformset_factory(
    parent_model=Tip,
    model=Code,
    form=CodeForm,
    extra=0,
    min_num=1,
    max_num=5,
    validate_min=True,
    validate_max=True
)


class TipForm(ModelFormWithFormSetMixin, forms.ModelForm):
    
    formset_class = CodeFormSet
    
    class Meta:
        model = Tip
        exclude = ('created_by', 'created_at', 'updated_at','has_tweeted')
        widgets = {
            'public_set': forms.RadioSelect,
            'tweet': forms.Textarea(),
        }

    def __init__(self, *args, **kwargs):
        # request.userをpublic_setのチェックで使用するため設定
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def clean_public_set(self):
        public_set = self.cleaned_data.get('public_set')
        if public_set == Tip.PRIVATE:
            private_count = Tip.objects.filter(created_by=self.request.user, public_set=Tip.PRIVATE).count()
            if private_count >= settings.PRIVATE_TIPS_MAXNUM:
                self.add_error('public_set', f'PrivateのTipの数が制限回数({settings.PRIVATE_TIPS_MAXNUM}回)に達しています。')
        return public_set
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', [])
        if len(tags) > 5:
            self.add_error('tags', 'タグは5個以下にしてください。')
        return tags


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    # saveメソッド(to_usersにnotification作成)
    def save_with_otherfields(self, request, tip, to_users_id=None):
        with transaction.atomic():
            comment = self.save(commit=False)
            comment.tip = tip
            comment.created_by = request.user
            comments = Comment.objects.filter(tip=tip).order_by('-no')
            if comments.exists():
                comment.no = comments.first().no + 1
            else:
                comment.no = 1
            comment.save()
            for to_user_id in (to_users_id or []):
                to_user = get_user_model().objects.get(id=to_user_id)
                comment.to_users.add(to_user)
                create_notification(request, to_user=to_user, category=Notification.COMMENT, tip=tip)
            comment.save()
        return comment
    
    # コメントチェック
    def clean_text(self):
        text = self.cleaned_data.get('text')
        if text in ('ばか', 'あほ', 'まぬけ', 'うんこ'):
            self.add_error('text', 'コメントに暴言を含めないでください。')
        return text


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label='名前')
    email = forms.EmailField(max_length=100, label='メールアドレス')
    message = forms.CharField(label='メッセージ', widget=forms.Textarea())
