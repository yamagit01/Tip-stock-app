from .models import Notification


def create_notification(request, to_user, category, tip=None, content=None):
    
    if to_user.is_active:
        if category == 'event':
            created_by = None
        else:
            created_by =request.user
            
        if content is None:
            content = ''
        
        Notification.objects.create(
            to_user=to_user,
            category=category,
            tip=tip,
            content=content,
            created_by=created_by
        )
