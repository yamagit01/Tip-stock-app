from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)

from .forms import CommentForm, TipForm
from .models import Tip


class IndexView(TemplateView):
    template_name = 'app/index.html'


class TipCreate(LoginRequiredMixin, CreateView):
    model = Tip
    form_class = TipForm

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
        if obj.created_by != self.request.user and obj.public_set == 'private':
            raise PermissionDenied('そのページは非公開です。')
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        return context


# TODO TipListとTipPublicListを１つにし、request.pathで処理を切り分け
class TipList(LoginRequiredMixin, ListView):
    model = Tip
    paginate_by = 6

    def get_queryset(self):
        queryset = Tip.objects.filter(created_by=self.request.user)
        query = self.request.GET.get('query')
        tagquery = self.request.GET.get('tagquery')

        # 検索条件の指定があればfilter
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        if tagquery:
            queryset = queryset.filter(tags__name__icontains=tagquery)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Tips'
        return context


class TipPublicList(LoginRequiredMixin, ListView):
    model = Tip
    paginate_by = 6

    def get_queryset(self):
        queryset = Tip.objects.filter(public_set='public')
        query = self.request.GET.get('query')
        tagquery = self.request.GET.get('tagquery')

        # 検索条件の指定があればfilter
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        if tagquery:
            queryset = queryset.filter(tags__name__icontains=tagquery)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Public Tips'
        return context


class TipUpdate(LoginRequiredMixin, UpdateView):
    model = Tip
    form_class = TipForm

    def get_object(self):  # TODO UserPassesTestMixinでclassを作成し継承するよう修正
        obj = super().get_object()
        # created_by!=request.user は更新不可
        if obj.created_by != self.request.user:
            raise PermissionDenied('そのページは編集できません')
        return obj

    def get_success_url(self):
        messages.info(self.request, 'Tipを更新しました。')
        return resolve_url('app:tip_detail', pk=self.kwargs['pk'])


class TipDelete(LoginRequiredMixin, DeleteView):
    model = Tip

    def get_object(self):  # TODO UserPassesTestMixinでclassを作成し継承するよう修正
        obj = super().get_object()
        # created_by!=request.user は削除不可
        if obj.created_by != self.request.user:
            raise PermissionDenied('そのページは削除できません。')
        return obj

    def get_success_url(self):
        messages.info(self.request, 'Tipを削除しました。')
        return resolve_url('app:tip_list')

@login_required
def add_comment(request, pk):
    tip = get_object_or_404(Tip, pk=pk)
    if tip.public_set == 'private':
            raise PermissionDenied('そのページにはコメントできません。')
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form.save_with_otherfields(tip, request.user)
            messages.success(request, 'コメントを追加しました。')
            return redirect('app:tip_detail', pk=pk)
        else:
            #  formのエラーを表示
            return render(request, 'app/tip_detail.html', context={
                'object': tip,
                'form': form,
            })

    return redirect('app:tip_detail', pk=pk)
