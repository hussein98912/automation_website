from django.urls import path,include
from .views import signup_api, login_api, logout_api,CategoryListAPIView, ServiceViewSet,ProjectViewSet
from . import views
from rest_framework import routers



router = routers.DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'projects', ProjectViewSet)



urlpatterns = [
    path("api/signup/", signup_api, name="api_signup"),
    path("api/login/", login_api, name="api_login"),
    path("api/logout/", logout_api, name="api_logout"),
    path('api/categories/', CategoryListAPIView.as_view(), name='categories-list'),
    path('orders/', views.create_order, name='create_order'),
    path('', include(router.urls)),
]