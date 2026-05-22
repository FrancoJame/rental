from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from django.core.mail import send_mail
from django.conf import settings
from .models import Listing, Message, LandlordProfile, EmailVerification, User
from .forms import LandlordRegisterForm, ListingForm, MessageForm

"""
View functions for the listings app.
Handles all business logic for displaying listings, details, messaging, registration, etc.
"""


def get_landlord_profile(user):
    """Return the landlord profile for a user, creating one if the user is a landlord and missing the profile."""
    if user.role != User.LANDLORD:
        return None
    profile, _ = LandlordProfile.objects.get_or_create(user=user)
    return profile

# 1. Public home page with filters
def home_page(request):
    # Retrieve all available listings
    listings = Listing.objects.filter(is_available=True)
    
    # Get all distinct locations currently listed (for filter dropdown)
    existing_locations = Listing.objects.filter(is_available=True).values_list('location', flat=True).distinct()
    # Normalize locations: strip whitespace and get distinct list
    location_list = sorted(list(set(loc.strip() for loc in existing_locations if loc)))
    
    # Find max price in database for the range slider default
    max_db_price = Listing.objects.filter(is_available=True).aggregate(Max('price_per_month'))['price_per_month__max'] or 2000000
    
    # Get filters from request
    search_location = request.GET.get('location', '').strip()
    room_type = request.GET.get('room_type', '')
    price_max = request.GET.get('price_max', '')
    
    # Apply filters
    if search_location:
        listings = listings.filter(location__icontains=search_location)
        
    if room_type:
        listings = listings.filter(room_type=room_type)
        
    if price_max:
        try:
            listings = listings.filter(price_per_month__lte=int(price_max))
        except ValueError:
            pass

    context = {
        'listings': listings,
        'location_list': location_list,
        'selected_location': search_location,
        'selected_room_type': room_type,
        'selected_price_max': price_max,
        'max_price_limit': max_db_price,
    }
    return render(request, 'listings/home.html', context)


# 2. Detailed listing view
def listing_detail(request, pk):
    """
    Show details for a single house listing.
    """
    # Landlord can view their own listing even if marked as taken (is_available=False)
    listing = get_object_or_404(Listing, pk=pk)
    if not listing.is_available and (not request.user.is_authenticated or listing.landlord != request.user):
        messages.warning(request, "This listing is no longer available.")
        return redirect('home')
        
    context = {
        'listing': listing
    }
    return render(request, 'listings/detail.html', context)


# 3. Landlord Registration
def landlord_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = LandlordRegisterForm(request.POST)
        if form.is_valid():
            # Create the user and landlord profile, then send verification
            user = form.save()
            national_id = form.cleaned_data.get('national_id_number')

            # Create email verification record
            email_verification = EmailVerification.objects.create(user=user)
            verification_code = email_verification.generate_code()
            
            # Send verification email to user
            user_subject = "Dream House Uganda - Email Verification"
            user_message = f"""
Dear {user.first_name},

Welcome to Dream House Uganda! Your landlord account has been created successfully.

To complete your registration and access your dashboard, enter the 6-digit verification code sent to the email address you registered with.

Verification code: {verification_code}

This code will expire in 15 minutes.

If you did not create this account, please contact us immediately.

Best regards,
Dream House Uganda Team
            """
            
            # Send verification email to admin
            admin_subject = f"New Landlord Registration - {user.first_name} {user.last_name}"
            admin_message = f"""
A new landlord has registered on Dream House Uganda:

Name: {user.first_name} {user.last_name}
Username: {user.username}
Email: {user.email}
National ID: {national_id}
Registration Time: {user.date_joined}

Please verify this user in the admin panel.

Best regards,
Dream House Uganda System
            """
            
            try:
                # Send to user
                send_mail(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                # Send to admin
                send_mail(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                
                messages.success(request, f"Account created! A verification code has been sent to {user.email}.")
                return redirect('verify_email', user_id=user.id)
            except Exception as e:
                messages.error(request, f"Account created, but we had trouble sending the verification email: {str(e)}")
                return redirect('verify_email', user_id=user.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LandlordRegisterForm()
        
    return render(request, 'listings/register.html', {'form': form})


# 3.5 Email Verification
def verify_email(request, user_id):
    """
    Email verification page where user enters the 6-digit code.
    """
    UserModel = get_user_model()
    
    try:
        user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        messages.error(request, "Invalid verification request.")
        return redirect('register')
    
    # Check if user is already verified
    if user.email_verification.is_verified:
        landlord_profile = get_landlord_profile(user)
        if landlord_profile is None:
            messages.error(request, "Only landlords may verify email for dashboard access.")
            return redirect('home')
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your email is already verified.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        code = request.POST.get('verification_code', '').strip()
        
        if not code:
            messages.error(request, "Please enter the 6-digit code.")
        elif len(code) != 6 or not code.isdigit():
            messages.error(request, "Please enter a valid 6-digit code.")
        else:
            email_verification = user.email_verification
            
            if email_verification.is_expired():
                messages.error(request, "Your verification code has expired. Please register again.")
                user.delete()
                return redirect('register')
            
            if email_verification.code == code:
                # Mark email as verified
                from django.utils import timezone
                email_verification.is_verified = True
                email_verification.verified_at = timezone.now()
                email_verification.save()
                
                # Mark landlord profile as verified
                landlord_profile = get_landlord_profile(user)
                if landlord_profile is None:
                    messages.error(request, "Unable to complete verification. Please contact support.")
                    return redirect('register')
                landlord_profile.email_verified = True
                landlord_profile.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, f"Welcome, {user.first_name}! Your email has been verified. You can now add your rental properties.")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid verification code. Please try again.")
    
    context = {
        'user': user,
        'user_id': user_id
    }
    return render(request, 'listings/verify_email.html', context)


# 4. Landlord Login
def landlord_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.role == User.MANAGER:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name or user.username}! You are logged in as General Manager.")
                    return redirect('/admin/')

                profile = get_landlord_profile(user)
                if profile and not profile.email_verified:
                    messages.warning(request, "Your account is not verified yet. Please enter the 6-digit code sent to your email.")
                    return redirect('verify_email', user_id=user.id)
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('dashboard')
            messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'listings/login.html', {'form': form})


# 5. Landlord Logout
@login_required
def landlord_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# 6. Landlord Dashboard
@login_required
def landlord_dashboard(request):
    profile = get_landlord_profile(request.user)
    if profile is None:
        messages.error(request, "Only landlords can access the dashboard. Please register as a landlord or return to the homepage.")
        return redirect('home')

    email_verified = profile.email_verified
    
    if not email_verified:
        messages.warning(request, "Please verify your email to add listings. Check your email for the verification code.")
    
    user_listings = Listing.objects.filter(landlord=request.user)
    
    # Calculate quick dashboard stats
    total_listings = user_listings.count()
    available_listings = user_listings.filter(is_available=True).count()
    taken_listings = total_listings - available_listings
    
    context = {
        'listings': user_listings,
        'total_listings': total_listings,
        'available_listings': available_listings,
        'taken_listings': taken_listings,
        'email_verified': email_verified
    }
    return render(request, 'listings/landlord_dashboard.html', context)


# 7. Add listing
@login_required
def house_create(request):
    profile = get_landlord_profile(request.user)
    if profile is None:
        messages.error(request, "Only landlords can add listings.")
        return redirect('home')

    # Check if email is verified
    if not profile.email_verified:
        messages.error(request, "Please verify your email before adding listings. Check your email inbox for the verification code.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.landlord = request.user
            listing.save()
            messages.success(request, f"New listing '{listing.title}' added successfully!")
            return redirect('dashboard')
        else:
            # Return form with errors to show to user on mobile
            messages.error(request, "Please fix the errors below and try again.")
            context = {'form': form, 'action': 'Add'}
            return render(request, 'listings/house_form.html', context)
    else:
        form = ListingForm()
        
    return render(request, 'listings/house_form.html', {'form': form, 'action': 'Add'})


# 8. Edit listing
@login_required
def house_update(request, pk):
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, f"Listing '{listing.title}' updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Failed to update listing. Please check the fields.")
    else:
        form = ListingForm(instance=listing)
        
    return render(request, 'listings/house_form.html', {'form': form, 'action': 'Edit', 'listing': listing})


# 9. Delete listing
@login_required
def house_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    if request.method == 'POST':
        title = listing.title
        listing.delete()
        messages.success(request, f"Listing '{title}' deleted successfully.")
    return redirect('dashboard')


# 10. Toggle Listing Availability (taken / available)
@login_required
def toggle_availability(request, pk):
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    listing.is_available = not listing.is_available
    listing.save()
    status = "Available" if listing.is_available else "Taken"
    messages.success(request, f"Listing '{listing.title}' is now marked as {status}.")
    return redirect('dashboard')


# 11. About Page
def about_page(request):
    return render(request, 'listings/about.html')


# 12. Contact Page
def contact_page(request):
    return render(request, 'listings/contact.html')


# 13. Policy Guidelines Page
def policy_page(request):
    return render(request, 'listings/policy.html')


# 14. Send Message to Landlord
def send_message(request, pk):
    """
    Handle sending a message from a customer to a landlord for a specific listing.
    """
    listing = get_object_or_404(Listing, pk=pk)
    
    if request.method == 'POST':
        data = request.POST.copy()
        # If offered_price is empty, set it to the listing price
        if not data.get('offered_price'):
            data['offered_price'] = listing.price_per_month
        form = MessageForm(data)
        if form.is_valid():
            message_obj = form.save(commit=False)
            message_obj.listing = listing
            message_obj.save()
            messages.success(request, "Your message has been sent to the landlord successfully!")
            return redirect('listing_detail', pk=pk)
        else:
            messages.error(request, "Please fill in all required fields correctly.")
    else:
        # Prefill offered_price with the listing price
        form = MessageForm(initial={'offered_price': listing.price_per_month})
    context = {
        'form': form,
        'listing': listing
    }
    return render(request, 'listings/send_message.html', context)


# 15. Landlord Messages
@login_required
def landlord_messages(request):
    # Get all messages for listings belonging to this landlord
    landlord_messages = Message.objects.filter(listing__landlord=request.user).select_related('listing').order_by('-created_at')
    
    # Count unread messages
    unread_count = landlord_messages.filter(is_read=False).count()
    
    # Mark all messages as read
    landlord_messages.filter(is_read=False).update(is_read=True)
    
    # Separate messages by response status
    pending_messages = landlord_messages.filter(landlord_response_sent=False)
    responded_messages = landlord_messages.filter(landlord_response_sent=True)
    
    context = {
        'messages': landlord_messages,
        'pending_messages': pending_messages,
        'responded_messages': responded_messages,
        'unread_count': unread_count
    }
    return render(request, 'listings/landlord_messages.html', context)


# 16. Mark Message as Responded
@login_required
def mark_message_responded(request, message_id):
    """
    Mark a customer message as responded by the landlord.
    Landlord can choose to respond via Email or WhatsApp
    """
    message = get_object_or_404(Message, id=message_id, listing__landlord=request.user)
    
    if request.method == 'POST':
        response_method = request.POST.get('response_method', 'email')
        
        if response_method not in ['email', 'whatsapp', 'both']:
            messages.error(request, "Invalid response method.")
            return redirect('landlord_messages')
        
        # Update message as responded
        from django.utils import timezone
        message.landlord_response_sent = True
        message.response_method = response_method
        message.response_date = timezone.now()
        message.save()
        
        messages.success(request, f"Message marked as responded via {response_method}.")
    
    return redirect('landlord_messages')


# 17. Message Detail View
@login_required
def message_detail(request, message_id):
    """
    Show detailed view of a single message with response tracking options.
    """
    message = get_object_or_404(Message, id=message_id, listing__landlord=request.user)
    
    # Mark as read
    message.is_read = True
    message.save()
    
    context = {
        'message': message,
        'sender_whatsapp_url': message.sender_whatsapp_url
    }
    return render(request, 'listings/message_detail.html', context)


