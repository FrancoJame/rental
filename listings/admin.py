from django.contrib import admin
from .models import Listing

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'room_type', 'price_per_month', 'location', 'landlord', 'is_available', 'created_at')
    list_filter = ('room_type', 'is_available', 'location', 'created_at')
    search_fields = ('title', 'location', 'description', 'telephone')
    raw_id_fields = ('landlord',)

