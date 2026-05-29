from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from django.core.mail import send_mail
from django.conf import settings
from .models import Listing, Message, LandlordProfile, EmailVerification, User
from .forms import LandlordRegisterForm, ListingForm, MessageForm, EmailVerificationForm


def get_landlord_profile(user):
    """Return the landlord profile for a user, creating one if missing."""
    if user.role != User.LANDLORD:
        return None
    profile, _ = LandlordProfile.objects.get_or_create(user=user)
    return profile


# 1. Public home page with filters
def home_page(request):
    listings = Listing.objects.filter(is_available=True)
    existing_locations = Listing.objects.filter(is_available=True).values_list('location', flat=True).distinct()
    location_list = sorted(list(set(loc.strip() for loc in existing_locations if loc)))
    max_db_price = Listing.objects.filter(is_available=True).aggregate(Max('price_per_month'))['price_per_month__max'] or 2000000

    search_location = request.GET.get('location', '').strip()
    room_type = request.GET.get('room_type', '')
    price_max = request.GET.get('price_max', '')

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
    listing = get_object_or_404(Listing, pk=pk)
    if not listing.is_available and (not request.user.is_authenticated or listing.landlord != request.user):
        messages.warning(request, "This listing is no longer available.")
        return redirect('home')
    return render(request, 'listings/detail.html', {'listing': listing})


# 3. Landlord Registration
def landlord_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LandlordRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            national_id = form.cleaned_data.get('national_id_number')

            email_verification = EmailVerification.objects.create(user=user)
            verification_code = email_verification.generate_code()

            user_subject = "Dream House Uganda - Email Verification"
            # Get landlord ID for email (generated just below)
            profile_for_email, _ = LandlordProfile.objects.get_or_create(user=user)
            if not profile_for_email.landlord_id:
                profile_for_email.landlord_id = LandlordProfile.generate_landlord_id()
                profile_for_email.save(update_fields=['landlord_id'])

            user_message = f"""
Dear {user.first_name},

Welcome to Dream House Uganda! Your landlord account has been created successfully.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR LANDLORD ID: {profile_for_email.landlord_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please save this ID. You will need it to contact support and verify your account.

To activate your account, enter the 6-digit verification code below:

Verification code: {verification_code}

This code will expire in 15 minutes.

If you did not create this account, please contact us immediately.

Best regards,
Dream House Uganda Team
            """

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

            # Generate unique Landlord ID (DH-AB1234 format) and save to profile
            profile, _ = LandlordProfile.objects.get_or_create(user=user)
            if not profile.landlord_id:
                profile.landlord_id = LandlordProfile.generate_landlord_id()
                profile.save(update_fields=['landlord_id'])

            try:
                send_mail(user_subject, user_message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL], fail_silently=False)
                messages.success(request, f"Account created! A verification code has been sent to {user.email}.")
            except Exception as e:
                messages.error(request, f"Account created, but we had trouble sending the verification email: {str(e)}")

            return redirect('verify_email', user_id=user.id)
    else:
        form = LandlordRegisterForm()

    return render(request, 'listings/register.html', {'form': form})


# 3.5 Email Verification helper
def send_verification_email(user, verification_code):
    subject = "Dream House Uganda - Email Verification"
    message = f"""
Dear {user.first_name},

Your new verification code is: {verification_code}

This code will expire in 15 minutes.

Best regards,
Dream House Uganda Team
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def verify_email(request, user_id):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        messages.error(request, "Invalid verification request.")
        return redirect('register')

    if user.email_verification.is_verified:
        landlord_profile = get_landlord_profile(user)
        if landlord_profile is None:
            messages.error(request, "Only landlords may verify email for dashboard access.")
            return redirect('home')
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your email is already verified.")
        return redirect('dashboard')

    form = EmailVerificationForm(request.POST or None)
    if request.method == 'POST':
        if 'resend_code' in request.POST:
            email_verification = user.email_verification
            verification_code = email_verification.generate_code()
            send_verification_email(user, verification_code)
            messages.success(request, "A new verification code has been sent to your email.")
            return redirect('verify_email', user_id=user_id)

        if form.is_valid():
            code = form.cleaned_data['verification_code']
            email_verification = user.email_verification

            if email_verification.is_expired():
                verification_code = email_verification.generate_code()
                send_verification_email(user, verification_code)
                messages.warning(request, "Your previous code expired. We've sent a fresh one to your email.")
                return redirect('verify_email', user_id=user_id)

            if email_verification.code == code:
                from django.utils import timezone
                email_verification.is_verified = True
                email_verification.verified_at = timezone.now()
                email_verification.save()

                landlord_profile = get_landlord_profile(user)
                if landlord_profile is None:
                    messages.error(request, "Unable to complete verification. Please contact support.")
                    return redirect('register')
                landlord_profile.email_verified = True
                landlord_profile.save()

                login(request, user)
                # Show the landlord ID prominently on first login
                try:
                    lid = user.landlord_profile.landlord_id or "N/A"
                except Exception:
                    lid = "N/A"
                messages.success(request, f"Welcome, {user.first_name}! Your email is verified. Your Landlord ID is {lid} — save it for future reference.")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid verification code. Please try again.")

    return render(request, 'listings/verify_email.html', {'user': user, 'user_id': user_id, 'form': form})


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
        messages.error(request, "Only landlords can access the dashboard.")
        return redirect('home')

    if not profile.email_verified:
        messages.warning(request, "Please verify your email to add listings. Check your email for the verification code.")

    user_listings = Listing.objects.filter(landlord=request.user)
    total_listings = user_listings.count()
    available_listings = user_listings.filter(is_available=True).count()
    taken_listings = total_listings - available_listings

    context = {
        'listings': user_listings,
        'total_listings': total_listings,
        'available_listings': available_listings,
        'taken_listings': taken_listings,
        'email_verified': profile.email_verified,
    }
    return render(request, 'listings/landlord_dashboard.html', context)


# 7. Add listing
@login_required
def house_create(request):
    profile = get_landlord_profile(request.user)
    if profile is None:
        messages.error(request, "Only landlords can add listings.")
        return redirect('home')

    if not profile.email_verified:
        messages.error(request, "Please verify your email before adding listings.")
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
            messages.error(request, "Please fix the errors below and try again.")
    else:
        form = ListingForm()

    return render(request, 'listings/house_form.html', {'form': form, 'action': 'Add'})


# 8. Edit listing
# FIX 3: Handle is_taken in the view so we control the flow cleanly.
@login_required
def house_update(request, pk):
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            updated_listing = form.save(commit=False)

            # FIX 3: If landlord marks as taken, delete the listing and redirect cleanly.
            if updated_listing.is_taken:
                title = listing.title
                listing.delete()
                messages.success(request, f"Listing '{title}' has been marked as taken and removed.")
                return redirect('dashboard')

            updated_listing.save()
            messages.success(request, f"Listing '{updated_listing.title}' updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Failed to update listing. Please check the fields.")
    else:
        form = ListingForm(instance=listing)

    # Always pass listing into context so existing images show correctly
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


# 10. Toggle Listing Availability — FIX 9: now requires POST
@login_required
def toggle_availability(request, pk):
    listing = get_object_or_404(Listing, pk=pk, landlord=request.user)
    if request.method == 'POST':
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


# 13. Policy Page
def policy_page(request):
    return render(request, 'listings/policy.html')


# 14. Send Message to Landlord
def send_message(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if request.method == 'POST':
        data = request.POST.copy()
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
        form = MessageForm(initial={'offered_price': listing.price_per_month})

    return render(request, 'listings/send_message.html', {'form': form, 'listing': listing})


# 15. Landlord Messages
@login_required
def landlord_messages(request):
    landlord_msgs = Message.objects.filter(listing__landlord=request.user).select_related('listing').order_by('-created_at')
    unread_count = landlord_msgs.filter(is_read=False).count()
    landlord_msgs.filter(is_read=False).update(is_read=True)

    pending_messages = landlord_msgs.filter(landlord_response_sent=False)
    responded_messages = landlord_msgs.filter(landlord_response_sent=True)

    context = {
        'messages': landlord_msgs,
        'pending_messages': pending_messages,
        'responded_messages': responded_messages,
        'unread_count': unread_count,
    }
    return render(request, 'listings/landlord_messages.html', context)


# 16. Mark Message as Responded
@login_required
def mark_message_responded(request, message_id):
    message = get_object_or_404(Message, id=message_id, listing__landlord=request.user)

    if request.method == 'POST':
        response_method = request.POST.get('response_method', 'email')
        if response_method not in ['email', 'whatsapp', 'both']:
            messages.error(request, "Invalid response method.")
            return redirect('landlord_messages')

        from django.utils import timezone
        message.landlord_response_sent = True
        message.response_method = response_method
        message.response_date = timezone.now()
        message.save()
        messages.success(request, f"Message marked as responded via {response_method}.")

    return redirect('landlord_messages')


# 17. Message Detail View — FIX 2: template now exists (message_detail.html created)
@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id, listing__landlord=request.user)
    message.is_read = True
    message.save()

    return render(request, 'listings/message_detail.html', {
        'message': message,
        'sender_whatsapp_url': message.sender_whatsapp_url,
    })
