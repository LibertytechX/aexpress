from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, LoginView, UserProfileView, LogoutView

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile endpoints
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('profile/', UserProfileView.as_view(), name='update_profile'),
]

