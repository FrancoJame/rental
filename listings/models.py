import re
import random
import urllib.parse
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

# ==========================================
# 1. CUSTOM USER MODEL (Three-Tier Architecture)
# ==========================================
class User(AbstractUser):
    CUSTOMER = 'customer'
    LANDLORD = 'landlord'
    MANAGER = 'manager'
    
    ROLE_CHOICES = [
        (CUSTOMER, 'Customer (Seeker)'),
        (LANDLORD, 'Landlord (Owner)'),
        (MANAGER, 'General Manager / Admin'),
    ]
    
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=CUSTOMER)
    
    # Global phone validation for standard structures (Uganda / International format strings)
    phone_regex = RegexValidator(
        regex=r'^\+?256\d{9}$|^0\d{9}$',
        message="Phone number must be valid Ugandan format: '07XXXXXXXX' or '+2567XXXXXXXX'."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically elevate General Managers to staff status for native admin access
        if self.role == self.MANAGER:
            self.is_staff = True
            self.is_superuser = True  # Gives full architectural control over site entries
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ==========================================
# 2. PROPERTY LISTING MODEL
# ==========================================
class Listing(models.Model):
    """
    Represents a rental house listing posted by a landlord.
    """
    ROOM_TYPES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('self_contained', 'Self-contained Room'),
    ]

    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings', limit_choices_to={'role': User.LANDLORD})
    title = models.CharField(max_length=200, help_text="Short descriptive title (e.g. Spacious Self-contained in Wandegeya)")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='single')
    price_per_month = models.PositiveIntegerField(help_text="Rent price per month in UGX")
    location = models.CharField(max_length=255, help_text="Exact location (e.g. Wandegeya, Kampala)")
    telephone = models.CharField(max_length=20, help_text="Contact telephone number (e.g. +256789000000)")
    
    # Three required images
    image_front = models.ImageField(upload_to='listings/images/', help_text="Front view of the house")
    image_inside = models.ImageField(upload_to='listings/images/', help_text="Inside view of the room")
    image_other = models.ImageField(upload_to='listings/images/', help_text="Any other view (e.g. compound or bathroom)")
    
    # Description and features
    description = models.TextField(help_text="Detailed description of the house")
    in_gate = models.BooleanField(default=False, verbose_name="Located inside a gate")
    inner_bathroom = models.BooleanField(default=False, verbose_name="Has inner bathroom")
    
    # Status and Time
    is_available = models.BooleanField(default=True, verbose_name="Available")
    is_taken = models.BooleanField(default=False, verbose_name="Marked as taken")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_room_type_display()} in {self.location} - UGX {self.price_per_month:,}"

    def clean(self):
        errors = {}
        
        # Validate price
        if self.price_per_month and self.price_per_month <= 0:
            errors['price_per_month'] = "Price must be greater than 0 UGX."
        if self.price_per_month and self.price_per_month > 999999999:
            errors['price_per_month'] = "Price limit exceeded."
        
        # Validate telephone
        if self.telephone and not self._validate_phone_number(self.telephone):
            errors['telephone'] = "Invalid phone number format. Use +2567... or 07..."
        
        # Validate length strings
        if self.title and len(self.title.strip()) < 10:
            errors['title'] = "Title must be at least 10 characters long."
        if self.location and len(self.location.strip()) < 3:
            errors['location'] = "Location must be at least 3 characters long."
        if self.description and len(self.description.strip()) < 20:
            errors['description'] = "Description must be at least 20 characters long."
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Professional fallback handling to remove house listing safely if checked as taken
        if self.is_taken and self.pk:
            self.delete()
            return
        self.full_clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _validate_phone_number(phone):
        digits = re.sub(r'\D', '', phone)
        return (len(digits) == 12 and digits.startswith('256')) or (len(digits) == 10 and digits.startswith('07'))

    @property
    def price_formatted(self):
        return f"UGX {self.price_per_month:,}"

    @property
    def whatsapp_url(self):
        digits_only = ''.join(c for c in self.telephone if c.isdigit())
        if digits_only.startswith('0'):
            clean_phone = '256' + digits_only[1:]
        elif digits_only.startswith('7') and len(digits_only) == 9:
            clean_phone = '256' + digits_only
        else:
            clean_phone = digits_only
            
        message = f"Hello! I saw your listing on Dream House Uganda for a {self.get_room_type_display()} in {self.location} ({self.price_formatted}/month). Is it still available?"
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/{clean_phone}?text={encoded_message}"


# ==========================================
# 3. PROFILE EXTENSIONS
# ==========================================
class LandlordProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='landlord_profile')
    national_id_number = models.CharField(max_length=20, blank=True, unique=True, null=True, help_text="National ID Number (NIN)")
    national_id_front = models.ImageField(upload_to='listings/national_ids/', blank=True, help_text="Upload the front of your national ID")
    national_id_back = models.ImageField(upload_to='listings/national_ids/', blank=True, help_text="Upload the back of your national ID")
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=20, blank=True)
    verification_requested_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Landlord Profile'
        verbose_name_plural = 'Landlord Profiles'

    def __str__(self):
        return f"{self.user.username} Landlord Profile"

    def generate_verification_code(self):
        self.verification_code = get_random_string(8).upper()
        self.save(update_fields=['verification_code'])
        return self.verification_code


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=15)
    
    def generate_code(self):
        self.code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.save()
        return self.code
    
    def __str__(self):
        return f"Verification for {self.user.email}"


# ==========================================
# 4. CUSTOMER MESSAGING SYSTEM
# ==========================================
class Message(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='messages')
    
    # Thread Actors mapping
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True, help_text="Registered user sender tracking link (optional)")
    sender_name = models.CharField(max_length=100, help_text="Your full name")
    sender_email = models.EmailField(help_text="Your email address")
    sender_phone = models.CharField(max_length=20, help_text="Your phone number")
    
    offered_price = models.PositiveIntegerField(null=True, blank=True, help_text="Price customer is willing to pay (optional)")
    message_text = models.TextField(help_text="Your message to the landlord")
    is_read = models.BooleanField(default=False, verbose_name="Read by landlord")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Landlord Response Management
    landlord_response_sent = models.BooleanField(default=False, verbose_name="Landlord responded")
    response_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Email & WhatsApp')
    ], null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer Message'
        verbose_name_plural = 'Customer Messages'
    
    def clean(self):
        errors = {}
        if not self.sender_name or len(self.sender_name.strip()) < 2:
            errors['sender_name'] = "Name must be at least 2 characters."
        if not self.message_text or len(self.message_text.strip()) < 10:
            errors['message_text'] = "Message content must be at least 10 characters long."
        if self.offered_price is not None and self.offered_price <= 0:
            errors['offered_price'] = "Offered price structure invalid."
            
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Message from {self.sender_name} to Landlord ({self.listing.landlord.username})"
    
    @property
    def sender_whatsapp_url(self):
        digits_only = ''.join(c for c in self.sender_phone if c.isdigit())
        if digits_only.startswith('0'):
            clean_phone = '256' + digits_only[1:]
        elif digits_only.startswith('7') and len(digits_only) == 9:
            clean_phone = '256' + digits_only
        else:
            clean_phone = digits_only
            
        reply_msg = f"Hello {self.sender_name}, responding to your inquiry about the listing: {self.listing.title}."
        return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(reply_msg)}"


# ==========================================
# 5. DATA SIGNALS FOR PROFILE AUTOMATIONS
# ==========================================
@receiver(post_save, sender=User)
def create_user_profile_extensions(sender, instance, created, **kwargs):
    if created and instance.role == User.LANDLORD:
        LandlordProfile.objects.create(user=instance)