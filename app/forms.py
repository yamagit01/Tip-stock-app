from django import forms
from django.conf import settings
from django.forms.models import inlineformset_factory

from .models import Code, Comment, Tip
from .widgets import FileInputByOnlyfilename


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
    validate_min=1,
    validate_max=5
)


class TipForm(ModelFormWithFormSetMixin, forms.ModelForm):
    
    formset_class = CodeFormSet
    
    class Meta:
        model = Tip
        exclude = ('created_by', 'created_at', 'updated_at')
        widgets = {
            'public_set': forms.RadioSelect,
            'uploadfile': FileInputByOnlyfilename(),
        }

    def __init__(self, *args, **kwargs):
        # request.userをpublic_setのチェックで使用するため設定
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def clean_public_set(self):
        public_set = self.cleaned_data.get('public_set')
        if public_set == 'private':
            private_count = Tip.objects.filter(created_by=self.request.user, public_set='private').count()
            if private_count >= settings.PRIVATE_TIPS_LIMIT:
                self.add_error('public_set', 'PrivateのTipの数が制限回数(20回)に達しています。')
        return public_set


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    # saveメソッド
    def save_with_otherfields(self, tip, user, commit=True):
        comment = self.save(commit=False)
        comment.tip = tip
        comment.created_by = user
        comment.no = Comment.objects.filter(tip=tip).count() + 1
        if commit:
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