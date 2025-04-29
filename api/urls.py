from django.urls import path
from .views import LoginView
from .views import AssetWebhookView,filter_branch,asset_tag_generate,add_asset

urlpatterns = [
     path('login/', LoginView.as_view(), name='login'),
     path('assets/', AssetWebhookView.as_view()),
     path('filter/', filter_branch),
     path('asset_tag/', asset_tag_generate),
     path('add_asset/', add_asset),
     
     # path('download-assets/',download_assets, name='download_assets'),
     # path('asset_tag/',asset_tag_generate)
]
