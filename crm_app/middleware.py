from django.shortcuts import redirect
from django.urls import reverse
from datetime import datetime, timedelta
from django.conf import settings

class SessionExpirationMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        
    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                current_time = datetime.now()
                if (current_time - last_activity) > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    
                    del request.session['last_activity']
                    return redirect(reverse('login'))  
            request.session['last_activity'] = datetime.now()
        else:
            
            response = self.get_response(request)
            return response


