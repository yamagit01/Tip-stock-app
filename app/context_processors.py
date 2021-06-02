from django.conf import settings

from .models import Tip

def tips_count(request):
    #TODO 現状はprivate_tips_limitのみ使用だが、今後表示する場合に使用
    # user_tips = Tip.objects.filter(crated_by=request.user)
    # all_tips_count = user_tips.count()
    # private_tips_count = user_tips.filter(public_set='private').count()
    # public_tips_count = user_tips.filter(public_set='public').count()

    params = {
        # 'all_tips_count': all_tips_count,
        # 'private_tips_count': private_tips_count,
        # 'public_tips_count': public_tips_count,
        'private_tips_limit': settings.PRIVATE_TIPS_LIMIT,
        
    }

    return params
