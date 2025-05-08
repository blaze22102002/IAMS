from django.urls import path,include
from .urls import user_urls  # Importing user-specific URLs from user_urls.py

urlpatterns = [
    path('user/', include('user_urls')),
# Include URLs for user-related views
    # You can add other API-related paths here for other modules
]
