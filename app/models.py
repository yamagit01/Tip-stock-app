from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager


class Tip(models.Model):
    PRIVATE = 'private'
    PUBLIC = 'public'
    
    CHOICES_TYPE = (
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    )

    title = models.CharField(max_length=25)
    description = models.TextField()
    tags = TaggableManager()
    # TODO filenameを変更(ハッシュ化, uuid)
    uploadfile = models.FileField(upload_to='uploadfiles/', blank=True, null=True)
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
    

class Code(models.Model):
    tip = models.ForeignKey(Tip, related_name='codes', on_delete=models.CASCADE)
    filename = models.CharField(max_length=25, blank=True, null=True)
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
        
    def __str__(self):
        return f'{self.tip} - {self.no}'

        
    def get_absolute_url(self):
        return reverse('app:tip_detail', kwargs={'pk': self.tip.pk})
