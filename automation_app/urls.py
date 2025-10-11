from django.urls import path,include
from .views import signup_api, login_api, logout_api,CategoryListAPIView, ServiceViewSet,ProjectViewSet,chatbot_api,OrderViewSet
from . import views
from .views import CurrentUserView
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)




router = routers.DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r"orders", OrderViewSet, basename="order")



urlpatterns = [
    path("api/signup/", signup_api, name="api_signup"),
    path("api/login/", login_api, name="api_login"),
    path("api/logout/", logout_api, name="api_logout"),
    path('api/categories/', CategoryListAPIView.as_view(), name='categories-list'),
    path('api/chatbot/', chatbot_api, name='chatbot-api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/me/', CurrentUserView.as_view(), name='current_user'),
    path('', include(router.urls)),
]