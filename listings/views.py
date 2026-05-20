from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from .models import Listing, Message
from .forms import LandlordRegisterForm, ListingForm, MessageForm

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
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your landlord account has been created successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LandlordRegisterForm()
        
    return render(request, 'listings/register.html', {'form': form})


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
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('dashboard')
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
    user_listings = Listing.objects.filter(landlord=request.user)
    
    # Calculate quick dashboard stats
    total_listings = user_listings.count()
    available_listings = user_listings.filter(is_available=True).count()
    taken_listings = total_listings - available_listings
    
    context = {
        'listings': user_listings,
        'total_listings': total_listings,
        'available_listings': available_listings,
        'taken_listings': taken_listings
    }
    return render(request, 'listings/landlord_dashboard.html', context)


# 7. Add listing
@login_required
def house_create(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.landlord = request.user
            listing.save()
            messages.success(request, f"New listing '{listing.title}' added successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Failed to add listing. Please check the fields.")
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
    listing = get_object_or_404(Listing, pk=pk)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message_obj = form.save(commit=False)
            message_obj.listing = listing
            message_obj.save()
            messages.success(request, "Your message has been sent to the landlord successfully!")
            return redirect('listing_detail', pk=pk)
        else:
            messages.error(request, "Please fill in all required fields correctly.")
    else:
        form = MessageForm()
    
    context = {
        'form': form,
        'listing': listing
    }
    return render(request, 'listings/send_message.html', context)


# 15. Landlord Messages
@login_required
def landlord_messages(request):
    # Get all messages for listings belonging to this landlord
    landlord_messages = Message.objects.filter(listing__landlord=request.user).select_related('listing')
    
    # Count unread messages
    unread_count = landlord_messages.filter(is_read=False).count()
    
    # Mark all messages as read
    landlord_messages.filter(is_read=False).update(is_read=True)
    
    context = {
        'messages': landlord_messages,
        'unread_count': unread_count
    }
    return render(request, 'listings/landlord_messages.html', context)

