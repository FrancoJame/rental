from django import forms
from django.core.exceptions import ValidationError
from .models import User, Listing, Message, LandlordProfile
import re

# ==========================================
# 1. LANDLORD AUTHENTICATION & REGISTRATION
# ==========================================
class LandlordRegisterForm(forms.ModelForm):
    """
    Form for landlord registration, mapped cleanly to the Custom User model.
    Handles automated password hashing validation and verification profiles.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose Username'}),
        help_text="Alphanumeric characters and underscores only, 3-30 characters",
        min_length=3,
        max_length=30
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
        min_length=2,
        max_length=50
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        min_length=2,
        max_length=50
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0770000000'}),
        help_text="Primary phone used for system processes."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        help_text="Minimum 8 characters, include uppercase, lowercase, numbers, and special characters.",
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    national_id_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '13-digit National ID Number (NIN)'}),
        required=True,
        help_text="Your unique 13-character National ID Number",
        min_length=13,
        max_length=13
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another one.")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            digits = re.sub(r'\D', '', phone)
            if not ((len(digits) == 12 and digits.startswith('256')) or 
                    (len(digits) == 10 and digits.startswith('07'))):
                raise ValidationError("Invalid phone number. Use format like +256770000000 or 0770000000.")
        return phone
    
    def clean_national_id_number(self):
        national_id = self.cleaned_data.get('national_id_number')
        if national_id and len(national_id) != 13:
            raise ValidationError("National ID must be exactly 13 characters long.")
        if LandlordProfile.objects.filter(national_id_number=national_id).exists():
            raise ValidationError("This National ID number is already registered.")
        return national_id

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        if password:
            if len(password) < 8:
                self.add_error('password', "Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password):
                self.add_error('password', "Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', password):
                self.add_error('password', "Password must contain at least one lowercase letter.")
            if not re.search(r'[0-9]', password):
                self.add_error('password', "Password must contain at least one number.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                self.add_error('password', "Password must contain at least one special character (!@#$%^&*).")
        
        if first_name and not first_name.replace(' ', '').isalpha():
            self.add_error('first_name', "First name should only contain letters.")
        if last_name and not last_name.replace(' ', '').isalpha():
            self.add_error('last_name', "Last name should only contain letters.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = User.LANDLORD  # Enforces landlord role assignment on submission
        if commit:
            user.save()
            # Explicitly creates the profile layer using the cleaned national ID number
            LandlordProfile.objects.create(
                user=user,
                national_id_number=self.cleaned_data.get('national_id_number')
            )
        return user


# ==========================================
# 2. HOUSE PROPERTY POSTING MANAGEMENT
# ==========================================
class ListingForm(forms.ModelForm):
    """
    Form for creating or editing a house listing with comprehensive validation.
    """
    class Meta:
        model = Listing
        fields = [
            'title', 'room_type', 'price_per_month', 'location', 
            'telephone', 'image_front', 'image_inside', 'image_other', 
            'description', 'in_gate', 'inner_bathroom', 'is_available', 'is_taken'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Modern Self-contained Room near Makerere',
                'minlength': '10',
                'maxlength': '200'
            }),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'price_per_month': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Price per month in UGX',
                'min': '1',
                'max': '999999999'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Kikoni, Wandegeya, Kampala',
                'minlength': '3',
                'maxlength': '255'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. +256770000000 or 0770000000',
                'pattern': '^([+256][0-9]{9,}|07[0-9]{8})$'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe your house features (e.g. proximity to road, security, water, electricity)',
                'minlength': '20'
            }),
            'image_front': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image_inside': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image_other': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'in_gate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inner_bathroom': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_taken': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Check this if the house has been taken. The listing will be automatically deleted.'
            }),
        }
    
    def clean_price_per_month(self):
        price = self.cleaned_data.get('price_per_month')
        if price and price <= 0:
            raise ValidationError("Price must be greater than 0.")
        if price and price > 999999999:
            raise ValidationError("Price cannot exceed 999,999,999 UGX.")
        return price
    
    def clean_telephone(self):
        phone = self.cleaned_data.get('telephone')
        if phone:
            digits = re.sub(r'\D', '', phone)
            if not ((len(digits) == 12 and digits.startswith('256')) or 
                    (len(digits) == 10 and digits.startswith('07'))):
                raise ValidationError("Invalid phone number. Use format like +256770000000 or 0770000000.")
        return phone
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 10:
            raise ValidationError("Title must be at least 10 characters long.")
        return title
    
    def clean_location(self):
        location = self.cleaned_data.get('location')
        if location and len(location.strip()) < 3:
            raise ValidationError("Location must be at least 3 characters long.")
        return location
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 20:
            raise ValidationError("Description must be at least 20 characters long.")
        return description


# ==========================================
# 3. TENANT DIRECT COMMUNICATION PIPELINE
# ==========================================
class MessageForm(forms.ModelForm):
    """
    Form for sending a message to a landlord about a listing with validation.
    """
    class Meta:
        model = Message
        fields = ['sender_name', 'sender_email', 'sender_phone', 'offered_price', 'message_text']
        widgets = {
            'sender_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
                'minlength': '2',
                'maxlength': '100',
                'required': True
            }),
            'sender_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email address',
                'required': True
            }),
            'sender_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your phone number (e.g. +256789000000)',
                'pattern': '^([+256][0-9]{9,}|07[0-9]{8})$',
                'required': True
            }),
            'offered_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price you are willing to pay (optional)',
                'min': '1'
            }),
            'message_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your message to the landlord...',
                'minlength': '10',
                'required': True
            }),
        }
    
    def clean_sender_name(self):
        name = self.cleaned_data.get('sender_name')
        if name and len(name.strip()) < 2:
            raise ValidationError("Name must be at least 2 characters.")
        if name and not name.replace(' ', '').isalpha():
            raise ValidationError("Name should only contain letters and spaces.")
        return name
    
    def clean_sender_phone(self):
        phone = self.cleaned_data.get('sender_phone')
        if phone:
            digits = re.sub(r'\D', '', phone)
            if not ((len(digits) == 12 and digits.startswith('256')) or 
                    (len(digits) == 10 and digits.startswith('07'))):
                raise ValidationError("Invalid phone number. Use format like +256789000000 or 0789000000.")
        return phone
    
    def clean_offered_price(self):
        price = self.cleaned_data.get('offered_price')
        if price is not None and price <= 0:
            raise ValidationError("Offered price must be greater than 0.")
        return price
    
    def clean_message_text(self):
        message = self.cleaned_data.get('message_text')
        if message and len(message.strip()) < 10:
            raise ValidationError("Message must be at least 10 characters.")
        return message