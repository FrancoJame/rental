from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, LandlordProfile, EmailVerification, Message

# ==========================================
# CUSTOM ADMIN ACTIONS
# ==========================================
def delete_selected_listings(modeladmin, request, queryset):
    """Delete selected listings"""
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f"{count} listing(s) successfully deleted.")
delete_selected_listings.short_description = "Delete selected listings"


def mark_as_taken(modeladmin, request, queryset):
    """Mark listings as taken (which triggers auto-deletion)"""
    count = 0
    for listing in queryset:
        listing.is_taken = True
        listing.save()
        count += 1
    modeladmin.message_user(request, f"{count} listing(s) processed.")
mark_as_taken.short_description = "Mark as taken (auto-deletes listings)"


def mark_messages_as_read(modeladmin, request, queryset):
    """Mark messages as read"""
    updated = queryset.update(is_read=True)
    modeladmin.message_user(request, f"{updated} message(s) marked as read.")
mark_messages_as_read.short_description = "Mark selected messages as read"


def mark_messages_as_unread(modeladmin, request, queryset):
    """Mark messages as unread"""
    updated = queryset.update(is_read=False)
    modeladmin.message_user(request, f"{updated} message(s) marked as unread.")
mark_messages_as_unread.short_description = "Mark selected messages as unread"


# ==========================================
# TABULAR INLINES
# ==========================================
class LandlordProfileInline(admin.StackedInline):
    model = LandlordProfile
    can_delete = False
    verbose_name_plural = 'Landlord Profiles'
    exclude = ('national_id_front', 'national_id_back')


class ListingInline(admin.TabularInline):
    """
    FIXED INLINE: Corrected target to map the Listing to the Custom User model,
    eliminating the E202 validation error.
    """
    model = Listing
    extra = 0
    fields = ('title', 'room_type', 'price_per_month', 'location', 'is_available', 'created_at')
    readonly_fields = ('created_at', 'title', 'room_type', 'price_per_month', 'location', 'is_available')
    can_delete = True


class MessageInline(admin.TabularInline):
    """Inline admin for messages directly under listing detail dashboards"""
    model = Message
    extra = 0
    fields = ('sender_name', 'sender_email', 'is_read', 'created_at')
    readonly_fields = ('sender_name', 'sender_email', 'created_at')
    can_delete = True


# ==========================================
# CUSTOM USER MODEL CONFIGURATION
# ==========================================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'role', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Verification Metadata', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Configuration', {'fields': ('role', 'phone_number', 'email')}),
    )
    inlines = []

    def get_inline_instances(self, request, obj=None):
        # Dynamically append Landlord profiles & Landlord property listings only if the user is a Landlord
        if obj and obj.role == User.LANDLORD:
            return [LandlordProfileInline(self.model, self.admin_site), ListingInline(self.model, self.admin_site)]
        return []


# ==========================================
# ENHANCED CORE MODELS INTERFACES
# ==========================================
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'title_display',
        'landlord_display',
        'room_type',
        'price_formatted_view',
        'location',
        'status_display',
        'messages_count',
        'created_at_display'
    )
    list_filter = ('room_type', 'is_available', 'location', 'created_at', 'in_gate', 'inner_bathroom')
    search_fields = ('title', 'location', 'description', 'telephone', 'landlord__username', 'landlord__email')
    readonly_fields = ('created_at', 'updated_at', 'price_formatted_view')
    raw_id_fields = ('landlord',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('landlord', 'title', 'room_type', 'location')
        }),
        ('Pricing & Contact', {
            'fields': ('price_per_month', 'telephone')
        }),
        ('Images', {
            'fields': ('image_front', 'image_inside', 'image_other')
        }),
        ('Description & Features', {
            'fields': ('description', 'in_gate', 'inner_bathroom')
        }),
        ('Status', {
            'fields': ('is_available', 'is_taken')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [delete_selected_listings, mark_as_taken]
    inlines = [MessageInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def title_display(self, obj):
        return f"{obj.title[:50]}..." if len(obj.title) > 50 else obj.title
    title_display.short_description = 'Title'
    
    def landlord_display(self, obj):
        url = reverse('admin:listings_user_change', args=[obj.landlord.id])
        return format_html(
            '<a href="{}">{} ({})</a>',
            url,
            obj.landlord.get_full_name() or obj.landlord.username,
            obj.landlord.email
        )
    landlord_display.short_description = 'Landlord'
    
    def price_formatted_view(self, obj):
        return obj.price_formatted
    price_formatted_view.short_description = 'Price/Month'
    
    def status_display(self, obj):
        if obj.is_taken:
            return mark_safe('<span style="color: #999; font-weight: bold;">DELETED (Taken)</span>')
        elif obj.is_available:
            return mark_safe('<span style="color: green; font-weight: bold;">Available</span>')
        else:
            return mark_safe('<span style="color: red; font-weight: bold;">Not Available</span>')
    status_display.short_description = 'Status'
    
    def messages_count(self, obj):
        count = obj.messages.count()
        unread = obj.messages.filter(is_read=False).count()
        return format_html('<span title="Total/Unread">{}/{}</span>', count, unread)
    messages_count.short_description = 'Messages'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Posted'


@admin.register(LandlordProfile)
class LandlordProfileAdmin(admin.ModelAdmin):
    list_display = (
        'landlord_display',
        'landlord_email',
        'national_id_number',
        'email_verified_display',
        'is_verified_display',
        'listings_count',
        'joined_date'
    )
    list_filter = ('email_verified', 'is_verified', 'verification_requested_at')
    search_fields = ('user__username', 'user__email', 'national_id_number')
    readonly_fields = ('verification_requested_at', 'verified_at', 'user')
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('National ID Verification', {
            'fields': ('national_id_number',)
        }),
        ('Verification Status', {
            'fields': ('email_verified', 'is_verified')
        }),
        ('Verification Codes', {
            'fields': ('verification_code',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('verification_requested_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'verification_requested_at'
    
    def landlord_display(self, obj):
        url = reverse('admin:listings_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    landlord_display.short_description = 'Landlord'
    
    def landlord_email(self, obj):
        return obj.user.email
    landlord_email.short_description = 'Email'
    
    def email_verified_display(self, obj):
        if obj.email_verified:
            return mark_safe('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        return mark_safe('<span style="color: red; font-weight: bold;">✗ Not Verified</span>')
    email_verified_display.short_description = 'Email Verified'
    
    def is_verified_display(self, obj):
        if obj.is_verified:
            return mark_safe('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        return mark_safe('<span style="color: orange; font-weight: bold;">⊘ Pending</span>')
    is_verified_display.short_description = 'ID Verified'
    
    def listings_count(self, obj):
        count = obj.user.listings.count()
        available = obj.user.listings.filter(is_available=True).count()
        return format_html('<span title="Total/Available">{}/{}</span>', count, available)
    listings_count.short_description = 'Listings'
    
    def joined_date(self, obj):
        return obj.user.date_joined.strftime('%Y-%m-%d')
    joined_date.short_description = 'Joined'


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified_display', 'code_display', 'created_at', 'is_expired_display')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'code')
    readonly_fields = ('code', 'created_at', 'user')
    
    def is_verified_display(self, obj):
        if obj.is_verified:
            return mark_safe('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        return mark_safe('<span style="color: red; font-weight: bold;">✗ Pending</span>')
    is_verified_display.short_description = 'Status'
    
    def code_display(self, obj):
        return f"{obj.code[:2]}****" if obj.code else "-"
    code_display.short_description = 'Code'
    
    def is_expired_display(self, obj):
        if obj.is_expired():
            return mark_safe('<span style="color: red;">Expired</span>')
        return mark_safe('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = 'Expires In'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'sender_display',
        'listing_display',
        'read_status_display',
        'offered_price_display',
        'response_status_display',
        'created_at_display'
    )
    list_filter = ('is_read', 'created_at', 'landlord_response_sent', 'response_method')
    search_fields = ('sender_name', 'sender_email', 'sender_phone', 'message_text', 'listing__title', 'listing__landlord__username')
    readonly_fields = ('listing', 'sender_name', 'sender_email', 'sender_phone', 'message_text', 'created_at', 'sender_whatsapp_url')
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('sender_name', 'sender_email', 'sender_phone', 'sender_whatsapp_url')
        }),
        ('Listing & Message', {
            'fields': ('listing', 'message_text', 'offered_price')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Landlord Response', {
            'fields': ('landlord_response_sent', 'response_method', 'response_date')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    actions = [mark_messages_as_read, mark_messages_as_unread, delete_selected_listings]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def sender_display(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small><br/><small>{}</small>',
            obj.sender_name, obj.sender_email, obj.sender_phone
        )
    sender_display.short_description = 'From'
    
    def listing_display(self, obj):
        url = reverse('admin:listings_listing_change', args=[obj.listing.id])
        return format_html(
            '<a href="{}">{}</a><br/><small>by {}</small>',
            url,
            obj.listing.title[:50],
            obj.listing.landlord.get_full_name() or obj.listing.landlord.username
        )
    listing_display.short_description = 'Listing'
    
    def read_status_display(self, obj):
        if obj.is_read:
            return mark_safe('<span style="color: green; font-weight: bold;">✓ Read</span>')
        return mark_safe('<span style="color: red; font-weight: bold;">Unread</span>')
    read_status_display.short_description = 'Status'
    
    def offered_price_display(self, obj):
        return f"UGX {obj.offered_price:,}" if obj.offered_price else "-"
    offered_price_display.short_description = 'Offered Price'
    
    def response_status_display(self, obj):
        if obj.landlord_response_sent:
            method = obj.response_method or 'Unknown'
            date = obj.response_date.strftime('%Y-%m-%d %H:%M') if obj.response_date else ''
            return format_html('<span style="color: green; font-weight: bold;">✓ Responded</span><br/><small>{} on {}</small>', method, date)
        return mark_safe('<span style="color: orange;">Awaiting Response</span>')
    response_status_display.short_description = 'Landlord Response'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Sent'