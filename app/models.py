import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager


def _tip_uploadfile_upload_to(instance, filename):
    return f'uploadfiles/{str(uuid.uuid4())}-{filename}'


class Tip(models.Model):
    PRIVATE = 'private'
    PUBLIC = 'public'
    
    CHOICES_TYPE = (
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    )

    title = models.CharField(max_length=50)
    description = models.TextField()
    tags = TaggableManager()
    uploadfile = models.FileField(upload_to=_tip_uploadfile_upload_to, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(get_user_model(), related_name='created_tip', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    public_set = models.CharField(max_length=20, choices=CHOICES_TYPE, default=PRIVATE)
    

    class Meta:
        db_table = 'tip'
        ordering = ('-updated_at',)


    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('app:tip_detail', kwargs={'pk': self.pk})
    
    def like_count(self): # TODO annotateで書ける？
        count = Like.objects.filter(tip=self).count()
        return count
    
    def is_liked_by_user(self, user):
        return Like.objects.filter(created_by=user).filter(tip=self).exists()
    

class Code(models.Model):
    tip = models.ForeignKey(Tip, related_name='codes', on_delete=models.CASCADE)
    filename = models.CharField(max_length=30, blank=True, null=True)
    content = models.TextField()

    class Meta:
        db_table = 'code'
        
    def __str__(self):
        return f'{self.tip} - {self.filename}'

        
    def get_absolute_url(self):
        return reverse('app:tip_detail', kwargs={'pk': self.tip.pk})


class Comment(models.Model):
    tip = models.ForeignKey(Tip, related_name='comments', on_delete=models.CASCADE)
    no = models.IntegerField(default=0)
    text = models.TextField()
    created_by = models.ForeignKey(get_user_model(), related_name='created_comment', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment'
        ordering = ('tip', 'no')
        
    def __str__(self):
        return f'{self.tip} - {self.no}'

    def get_absolute_url(self):
        return reverse('app:tip_detail', kwargs={'pk': self.tip.pk})


class Like(models.Model):
    tip = models.ForeignKey(Tip, related_name='likes', on_delete=models.CASCADE)
    created_by = models.ForeignKey(get_user_model(), related_name='created_like', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'like'
        constraints = [
            models.UniqueConstraint(fields=['tip', 'created_by'], name='unique_like'),
        ]
        
    def __str__(self):
        return f'{self.tip} - {self.created_by.username}'

    def get_absolute_url(self):
        return reverse('app:tip_detail', kwargs={'pk': self.tip.pk})


class Notification(models.Model):
    COMMENT = 'comment'
    EVENT = 'event'
    
    # TODO 今後機能を追加したときに追加
    # MESSAGE = 'message'
    # FOLLOW = 'follow'

    CHOICES = (
        (COMMENT, 'コメント'),
        (EVENT, 'イベント'),
        # (MESSAGE, 'メッセージ'),
        # (FOLLOW, 'フォロー'),
    )

    to_user = models.ForeignKey(get_user_model(), related_name='notification_to', on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CHOICES)
    tip = models.ForeignKey(Tip, related_name='notifications', on_delete=models.CASCADE, blank=True, null=True)
    content = models.CharField(max_length=100, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), related_name='created_notification', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering =('is_read', '-created_at')
