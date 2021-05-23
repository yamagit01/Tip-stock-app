from django import forms
from django.forms.models import inlineformset_factory

from .models import Code, Tip


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
            'public_set': forms.RadioSelect
        }
