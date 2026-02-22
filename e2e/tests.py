from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from products.models.product import Product
from products.models.rating import Rating
from products.models.comment import Comment
from products.models.user import User


class CallCommandViewTestCase(APITestCase):
    def test_valid_command(self):
        url = reverse('call-command', kwargs={'command': 'check'})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

    def test_invalid_command(self):
        url = reverse('call-command', kwargs={'command': 'nonexistent_command_xyz'})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())


class ProductFlowE2ETestCase(APITestCase):
    def setUp(self):
        self.products_url = reverse('product-list')
        self.base_data = {
            'category': 'Energy Drink',
            'variant': 'Monster Ultra',
            'telegram_id': 111111111,
            'username': 'arina',
            'flavors': ['Watermelon'],
            'groups': ['Family'],
            'ratings': [
                {'telegram_id': 111111111, 'rating': 4},
                {'telegram_id': 222222222, 'rating': 3},
            ],
            'comments': [
                {'telegram_id': 111111111, 'comment': 'Pretty good'},
                {'telegram_id': 222222222, 'comment': 'Too sweet'},
            ],
        }

    def test_create_and_retrieve(self):
        self.client.post(self.products_url, self.base_data, format='json')

        response = self.client.get(self.products_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product = response.data[0]
        self.assertEqual(product['category'], 'Energy Drink')
        self.assertEqual(product['variant'], 'Monster Ultra')
        self.assertEqual(len(product['flavors']), 1)
        self.assertEqual(len(product['ratings']), 2)
        self.assertEqual(len(product['comments']), 2)

    def test_create_update_and_retrieve(self):
        create_response = self.client.post(self.products_url, self.base_data, format='json')
        product_id = create_response.data['id']
        detail_url = reverse('product-detail', kwargs={'product_id': product_id})

        self.client.put(detail_url, {'category': 'Soda', 'variant': 'Pepsi Max'}, format='json')

        response = self.client.get(self.products_url)
        product = response.data[0]
        self.assertEqual(product['category'], 'Soda')
        self.assertEqual(product['variant'], 'Pepsi Max')

    def test_create_and_delete(self):
        create_response = self.client.post(self.products_url, self.base_data, format='json')
        product_id = create_response.data['id']
        detail_url = reverse('product-detail', kwargs={'product_id': product_id})

        self.client.delete(detail_url)

        self.assertEqual(Product.objects.count(), 0)
        response = self.client.get(self.products_url)
        self.assertEqual(len(response.data), 0)

    def test_add_rating_after_creation(self):
        create_response = self.client.post(
            self.products_url,
            {'category': 'Energy Drink', 'telegram_id': 111111111},
            format='json',
        )
        product_id = create_response.data['id']
        User.objects.get_or_create(telegram_id=111111111)

        self.client.post(
            reverse('product-rating'),
            {'product_id': product_id, 'telegram_id': 111111111, 'rating': 5},
            format='json',
        )

        self.assertEqual(Rating.objects.filter(product_id=product_id).count(), 1)
        self.assertEqual(Rating.objects.get(product_id=product_id).value, 5)

    def test_add_comment_after_creation(self):
        create_response = self.client.post(
            self.products_url,
            {'category': 'Energy Drink', 'telegram_id': 111111111},
            format='json',
        )
        product_id = create_response.data['id']
        User.objects.get_or_create(telegram_id=111111111)

        self.client.post(
            reverse('product-comment'),
            {'product_id': product_id, 'telegram_id': 111111111, 'comment': 'Really nice'},
            format='json',
        )

        self.assertEqual(Comment.objects.filter(product_id=product_id).count(), 1)
        self.assertEqual(Comment.objects.get(product_id=product_id).text, 'Really nice')
