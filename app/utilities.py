from .models import Notification


def create_notification(request, to_user, category, tip=None, content=None):
    if category == 'event':
        created_by = None
    else:
        created_by =request.user
    
    notification = Notification.objects.create(
        to_user=to_user,
        category=category,
        tip=tip,
        content=content,
        created_by=created_by
    )
