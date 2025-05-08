# api/urls/admin_urls.py

from django.urls import path
from api.views.admin_views import AdminLoginView

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'),
    # path('webhook/', AssetWebhookView.as_view(), name='asset-webhook'),
]
