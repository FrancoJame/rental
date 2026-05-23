from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    # Customer views
    path('', views.home_page, name='home'),
    path('house/<int:pk>/', views.listing_detail, name='listing_detail'),
    
    # Landlord auth
    path('register/', views.landlord_register, name='register'),
    path('verify-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('login/', views.landlord_login, name='login'),
    path('login/admin/', RedirectView.as_view(url='/admin/', permanent=False), name='admin_redirect'),
    path('logout/', views.landlord_logout, name='logout'),
    
    # Static informational pages
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('policy/', views.policy_page, name='policy'),
    
    # Landlord management
    path('dashboard/', views.landlord_dashboard, name='dashboard'),
    path('house/add/', views.house_create, name='house_create'),
    path('house/<int:pk>/edit/', views.house_update, name='house_update'),
    path('house/<int:pk>/delete/', views.house_delete, name='house_delete'),
    path('house/<int:pk>/toggle/', views.toggle_availability, name='toggle_availability'),
    
    # Messaging
    path('house/<int:pk>/send-message/', views.send_message, name='send_message'),
    path('messages/', views.landlord_messages, name='landlord_messages'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/responded/', views.mark_message_responded, name='mark_message_responded'),
]
