from django.urls import path
from . import views

urlpatterns = [
    # Customer views
    path('', views.home_page, name='home'),
    path('house/<int:pk>/', views.listing_detail, name='listing_detail'),
    
    # Landlord auth
    path('register/', views.landlord_register, name='register'),
    path('login/', views.landlord_login, name='login'),
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
]
