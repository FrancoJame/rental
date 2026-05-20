from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Listing

class ListingModelTests(TestCase):
    def setUp(self):
        # Create a user (landlord)
        self.landlord = User.objects.create_user(
            username='testlandlord',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        
        # Mock simple images
        self.mock_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )

        # Create a listing
        self.listing = Listing.objects.create(
            landlord=self.landlord,
            title='Cosy Single Room',
            room_type='single',
            price_per_month=350000,
            location='Kikoni, Kampala',
            telephone='+256771234567',
            image_front=self.mock_image,
            image_inside=self.mock_image,
            image_other=self.mock_image,
            description='Close to the main road, in a gate, inner bathroom.',
            in_gate=True,
            inner_bathroom=True,
            is_available=True
        )

    def test_listing_string_representation(self):
        self.assertEqual(
            str(self.listing),
            "Single Room in Kikoni, Kampala - UGX 350,000"
        )

    def test_price_formatting(self):
        self.assertEqual(self.listing.price_formatted, "UGX 350,000")

    def test_whatsapp_url_generation(self):
        # Standard format
        self.assertIn("wa.me/256771234567", self.listing.whatsapp_url)
        self.assertIn("Kikoni%2C%20Kampala", self.listing.whatsapp_url)

    def test_whatsapp_url_local_number_formatting(self):
        # Number starting with 0
        self.listing.telephone = "0771234567"
        self.listing.save()
        self.assertIn("wa.me/256771234567", self.listing.whatsapp_url)
        
        # Number starting with 7
        self.listing.telephone = "771234567"
        self.listing.save()
        self.assertIn("wa.me/256771234567", self.listing.whatsapp_url)


class ListingViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.landlord = User.objects.create_user(
            username='testlandlord',
            password='testpassword123',
            first_name='John',
            last_name='Doe'
        )
        self.mock_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'dummyimgdata',
            content_type='image/jpeg'
        )

        # Create two listings in different locations and prices
        self.listing1 = Listing.objects.create(
            landlord=self.landlord,
            title='Single Room Kikoni',
            room_type='single',
            price_per_month=200000,
            location='Kikoni',
            telephone='+256771234567',
            image_front=self.mock_image,
            image_inside=self.mock_image,
            image_other=self.mock_image,
            is_available=True
        )
        self.listing2 = Listing.objects.create(
            landlord=self.landlord,
            title='Self contained Wandegeya',
            room_type='self_contained',
            price_per_month=600000,
            location='Wandegeya',
            telephone='+256771234567',
            image_front=self.mock_image,
            image_inside=self.mock_image,
            image_other=self.mock_image,
            is_available=True
        )
        self.listing3 = Listing.objects.create(
            landlord=self.landlord,
            title='Rented Out Room',
            room_type='double',
            price_per_month=400000,
            location='Kikoni',
            telephone='+256771234567',
            image_front=self.mock_image,
            image_inside=self.mock_image,
            image_other=self.mock_image,
            is_available=False  # Taken/Rented out
        )

    def test_home_page_displays_only_available_listings(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Single Room Kikoni')
        self.assertContains(response, 'Self contained Wandegeya')
        self.assertNotContains(response, 'Rented Out Room')

    def test_filter_by_location(self):
        response = self.client.get(reverse('home'), {'location': 'Kikoni'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Single Room Kikoni')
        self.assertNotContains(response, 'Self contained Wandegeya')

    def test_filter_by_room_type(self):
        response = self.client.get(reverse('home'), {'room_type': 'self_contained'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Single Room Kikoni')
        self.assertContains(response, 'Self contained Wandegeya')

    def test_filter_by_max_price(self):
        response = self.client.get(reverse('home'), {'price_max': '300000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Single Room Kikoni')
        self.assertNotContains(response, 'Self contained Wandegeya')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

