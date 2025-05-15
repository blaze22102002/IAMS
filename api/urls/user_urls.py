# import os
# print("Current working dir:", os.getcwd())


from django.urls import path
from api.views.user_views import UserLoginView, BranchFilterView,asset_tag_generate,AssetAdditionView,AssetUpdateView,AssetExportStreamView


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('filter/', BranchFilterView.as_view(), name='filter-branch'),
    path('asset_tag/', asset_tag_generate, name='filter-branch'),
    path('asset/add/', AssetAdditionView.as_view(), name='asset-add'),
    path('asset/update/', AssetUpdateView.as_view(), name='asset-update'),
    path('asset/export/', AssetExportStreamView.as_view(), name='export-assets'),

]
