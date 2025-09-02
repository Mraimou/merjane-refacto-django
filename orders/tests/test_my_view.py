from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from orders.entities.product import Product
from orders.entities.order import Order
from ..my_views import OrderProcessor

class TestMyView(TestCase):
    @classmethod
    def setUpTestData(cls):
        # On crée une liste de produits + order une seule fois pour toute la classe de tests.
        normal_product = Product(available=15, lead_time=30, type="NORMAL", name="USB Cable")
        products = [
            normal_product,
            Product(available=10, lead_time=0, type="NORMAL", name="USB Dongle"),
            Product(available=15, lead_time=30, type="EXPIRABLE", name="Butter",
                    expiry_date=date.today() + timedelta(days=26)),
            Product(available=90, lead_time=6, type="EXPIRABLE", name="Milk",
                    expiry_date=date.today() - timedelta(days=2)),
            Product(available=15, lead_time=30, type="SEASONAL", name="Watermelon",
                    season_start_date=date.today() - timedelta(days=2),
                    season_end_date=date.today() + timedelta(days=58)),
            Product(available=15, lead_time=30, type="SEASONAL", name="Grapes",
                    season_start_date=date.today() + timedelta(days=180),
                    season_end_date=date.today() + timedelta(days=240)),
        ]
        cls.normal_product = normal_product
        for p in products:
            p.save()
        order = Order.objects.create()
        order.products.set(products)
        cls.order = order

    @patch('orders.my_views.ps')
    def test_process_order_should_return(self, mock_ns):
        url = reverse('process_order', args=[self.order.id])
        response = self.client.post(url, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        result_order = Order.objects.get(id=self.order.id)
        self.assertEqual(result_order.id, self.order.id)

    # Seasonal items tests

    # EXPIRABLE items tests

    # NORMAL items tests
    @patch('orders.my_views.ps')
    def test_process_normal(self, mock_ns):
        processor = OrderProcessor(self.order)
        processor._process_normal(self.normal_product)
        self.assertEqual(self.normal_product.available, 14)



