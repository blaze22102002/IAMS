# import os
# print("Current working dir:", os.getcwd())


from django.urls import path
from api.views.user_views import UserLoginView, BranchFilterView


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('filter-branch/', BranchFilterView.as_view(), name='filter-branch'),
]
