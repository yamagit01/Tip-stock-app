from django.conf import settings

from .models import Tip


def tips_count(request):
    #TODO 現状はprivate_tips_maxnumのみ使用だが、今後表示する場合に使用
    # user_tips = Tip.objects.filter(crated_by=request.user)
    # all_tips_count = user_tips.count()
    # private_tips_count = user_tips.filter(public_set=Tip.Private).count()
    # public_tips_count = user_tips.filter(public_set=Tip.PUBLIC).count()

    params = {
        # 'all_tips_count': all_tips_count,
        # 'private_tips_count': private_tips_count,
        # 'public_tips_count': public_tips_count,
        'private_tips_maxnum': settings.PRIVATE_TIPS_MAXNUM,
        
    }

    return params


def notifications_count(request):
    if request.user.is_authenticated:
        return {'notifications_count': request.user.notification_to.filter(is_read=False).count}
    else:
        return {'notifications_count': 0}
