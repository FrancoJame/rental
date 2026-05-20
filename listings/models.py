from django.db import models
from django.contrib.auth.models import User
import urllib.parse

class Listing(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

