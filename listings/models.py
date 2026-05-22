from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
import urllib.parse
import re

class Listing(models.Model):
    """
    Represents a rental house listing posted by a landlord.
    """
    ROOM_TYPES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('self_contained', 'Self-contained Room'),
    ]

    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
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
    
    def clean(self):
        """Validate model fields"""
        errors = {}
        
        # Validate price
        if self.price_per_month <= 0:
            errors['price_per_month'] = "Price must be greater than 0"
        if self.price_per_month > 999999999:
            errors['price_per_month'] = "Price is too high"
        
        # Validate telephone
        if not self._validate_phone_number(self.telephone):
            errors['telephone'] = "Invalid phone number format (e.g. +256789000000 or 0789000000)"
        
        # Validate title
        if not self.title or len(self.title.strip()) < 10:
            errors['title'] = "Title must be at least 10 characters long"
        
        # Validate location
        if not self.location or len(self.location.strip()) < 3:
            errors['location'] = "Location must be at least 3 characters long"
        
        # Validate description
        if not self.description or len(self.description.strip()) < 20:
            errors['description'] = "Description must be at least 20 characters long"
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Auto-delete listing when marked as taken"""
        if self.is_taken and self.pk:
            # Listing is being marked as taken - delete it
            self.delete()
            return
        self.full_clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _validate_phone_number(phone):
        """Validate Uganda phone number formats"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Valid Uganda numbers: 256XXXXXXXXX (12 digits) or 07XXXXXXXXX (10 digits starting with 07)
        return (len(digits) == 12 and digits.startswith('256')) or (len(digits) == 10 and digits.startswith('07'))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_room_type_display()} in {self.location} - UGX {self.price_per_month:,}"

    @property
    def price_formatted(self):
        return f"UGX {self.price_per_month:,}"

    @property
    def whatsapp_url(self):
        # Format the phone number to start with Uganda code 256 if needed
        digits_only = ''.join(c for c in self.telephone if c.isdigit())
        if digits_only.startswith('0'):
            clean_phone = '256' + digits_only[1:]
        elif digits_only.startswith('7') and len(digits_only) == 9:
            clean_phone = '256' + digits_only
        else:
            clean_phone = digits_only
            
        message = f"Hello! I saw your listing on Dream House Uganda for a {self.get_room_type_display()} in {self.location} (UGX {self.price_per_month:,}/month). Is it still available?"
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/{clean_phone}?text={encoded_message}"


class LandlordProfile(models.Model):
    """
    Stores additional information and verification for landlord users.
    """
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
        return f"{self.user.username} landlord profile"

    def generate_verification_code(self):
        self.verification_code = get_random_string(8).upper()
        self.save(update_fields=['verification_code'])
        return self.verification_code


class EmailVerification(models.Model):
    """
    Stores 6-digit email verification codes for new landlord registrations.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def is_expired(self):
        """Check if verification code is older than 15 minutes"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=15)
    
    def generate_code(self):
        """Generate a random 6-digit code"""
        import random
        self.code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.save()
        return self.code
    
    def __str__(self):
        return f"Verification for {self.user.email}"


class Message(models.Model):
    """
    Stores messages sent by customers to landlords about a specific listing.
    Includes landlord response tracking via email and WhatsApp.
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='messages')
    sender_name = models.CharField(max_length=100, help_text="Your full name")
    sender_email = models.EmailField(help_text="Your email address")
    sender_phone = models.CharField(max_length=20, help_text="Your phone number")
    offered_price = models.PositiveIntegerField(null=True, blank=True, help_text="Price customer is willing to pay (optional)")
    message_text = models.TextField(help_text="Your message to the landlord")
    is_read = models.BooleanField(default=False, verbose_name="Read by landlord")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Landlord response tracking
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
        """Validate message fields"""
        errors = {}
        
        # Validate sender name
        if not self.sender_name or len(self.sender_name.strip()) < 2:
            errors['sender_name'] = "Name must be at least 2 characters"
        
        # Validate message text
        if not self.message_text or len(self.message_text.strip()) < 10:
            errors['message_text'] = "Message must be at least 10 characters"
        
        # Validate offered price if provided
        if self.offered_price is not None and self.offered_price <= 0:
            errors['offered_price'] = "Price must be greater than 0"
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Save with validation"""
        self.full_clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Message from {self.sender_name} about {self.listing.title}"
    
    @property
    def sender_whatsapp_url(self):
        """Generate WhatsApp contact URL for the sender"""
        digits_only = ''.join(c for c in self.sender_phone if c.isdigit())
        if digits_only.startswith('0'):
            clean_phone = '256' + digits_only[1:]
        elif digits_only.startswith('7') and len(digits_only) == 9:
            clean_phone = '256' + digits_only
        else:
            clean_phone = digits_only
        return f"https://wa.me/{clean_phone}"


@receiver(post_save, sender=User)
def create_landlord_profile(sender, instance, created, **kwargs):
    if created:
        LandlordProfile.objects.create(user=instance)

