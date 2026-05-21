from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

app_name = 'accounts'

urlpatterns = [
    # =====================================================
    # AUTHENTICATION ENDPOINTS
    # =====================================================
    path('register/', views.register, name='register'),
    path('login/', views.login_with_email, name='login'),
    path('me/', views.me, name='me'),
    path('change-password/', views.change_password, name='change_password'),
    
    # JWT Token Management
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # =====================================================
    # PASSWORD RESET ENDPOINTS
    # =====================================================
    path('password/reset/', views.password_reset_request, name='password_reset_request'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # =====================================================
    # ROLE MANAGEMENT ENDPOINTS
    # =====================================================
    path('roles/', views.roles_list_create, name='roles_list_create'),
    path('roles/<int:pk>/', views.role_detail, name='role_detail'),
    
    # =====================================================
    # PERMISSION MANAGEMENT ENDPOINTS
    # =====================================================
    path('permissions/', views.permissions_list_create, name='permissions_list_create'),
    path('permissions/<int:pk>/', views.permission_detail, name='permission_detail'),
    
    # =====================================================
    # USER MANAGEMENT ENDPOINTS (ADMIN)
    # =====================================================
    path('users/', views.users_list, name='users_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),

    # =====================================================
    # AGENCY MANAGEMENT ENDPOINTS
    # =====================================================
    path('agencies/', views.agencies_list_create, name='agencies_list_create'),
    path('agencies/<int:pk>/', views.agency_detail, name='agency_detail'),
]