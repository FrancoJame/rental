from django import forms
from django.contrib.auth.models import User
from .models import Listing

class LandlordRegisterForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose Username'}),
        help_text=""
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        help_text="Must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        if password and len(password) < 8:
            self.add_error('password', "Password must be at least 8 characters long.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title', 'room_type', 'price_per_month', 'location', 
            'telephone', 'image_front', 'image_inside', 'image_other', 
            'description', 'in_gate', 'inner_bathroom', 'is_available'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Modern Self-contained Room near Makerere'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'price_per_month': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per month in UGX'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Kikoni, Wandegeya, Kampala'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +256770000000'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your house features (e.g. proximity to road, security, water, electricity)'}),
            'image_front': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'onchange': 'previewImage(this, "front-preview")'}),
            'image_inside': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'onchange': 'previewImage(this, "inside-preview")'}),
            'image_other': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'onchange': 'previewImage(this, "other-preview")'}),
            'in_gate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inner_bathroom': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
