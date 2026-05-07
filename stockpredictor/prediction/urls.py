from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),  #  Fixed from 'register'
    path('logout/', views.logout_view, name='logout'),
    

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # # Main App Features
    path('predict/', views.stock_prediction_view, name='predict_stock'),  
    path('history/', views.prediction_history, name='prediction_history'),
    
    path("watchlist/", views.watchlist_view, name="watchlist"),

    # AJAX / API endpoints
    path("watchlist/add/", views.watchlist_add, name="watchlist_add"),
    path("watchlist/<int:pk>/remove/", views.watchlist_remove, name="watchlist_remove"),
    path("watchlist/<int:pk>/toggle-pin/", views.watchlist_toggle_pin, name="watchlist_toggle_pin"),
    path("watchlist/<int:pk>/update/", views.watchlist_update_item, name="watchlist_update_item"),
    path("watchlist/refresh/", views.watchlist_refresh, name="watchlist_refresh"),
    path("watchlist/spark/<int:pk>/", views.watchlist_spark, name="watchlist_spark"),

    # bulk
    path("watchlist/import/", views.watchlist_import, name="watchlist_import"),
    path("watchlist/export/", views.watchlist_export, name="watchlist_export"),
    # path("watchlist/", views.watchlist_view, name="watchlist"),

    # # AJAX / API endpoints
    # path("watchlist/add/", views.watchlist_add, name="watchlist_add"),
    # path("watchlist/<int:pk>/remove/", views.watchlist_remove, name="watchlist_remove"),
    # path("watchlist/<int:pk>/toggle-pin/", views.watchlist_toggle_pin, name="watchlist_toggle_pin"),
    # path("watchlist/<int:pk>/update/", views.watchlist_update_item, name="watchlist_update_item"),
    # path("watchlist/refresh/", views.watchlist_refresh, name="watchlist_refresh"),
    # path("watchlist/spark/<int:pk>/", views.watchlist_spark, name="watchlist_spark"),

    # bulk
    # path("watchlist/import/", views.watchlist_import, name="watchlist_import"),
    # path("watchlist/export/", views.watchlist_export, name="watchlist_export"),
    # path('profile/edit/', views.edit_profile, name='edit_profile'),
    # path('profile/delete/', views.delete_account, name='delete_account'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    # path("api/stock-data/<str:symbol>/", views.stock_data_api, name="stock_data_api"),
    #graph
    re_path(r"^api/stock-data/(?P<symbol>[\w\.\-]+)/$", views.stock_data, name="stock-data"),
    # profile
    path("profile/", views.profile_settings, name="profile"),
    path("api/stock-info/<str:symbol>/", views.stock_info_api, name="stock_info_api"),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)