from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import User, ExchangeTransaction
from datetime import timedelta
from django.utils import timezone

class QuoteExchangeRateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quote_exchange_rate')

    def test_quote_exchange_rate_success(self):
        response = self.client.get(self.url, {'from_currency': 'USD', 'to_currency': 'EUR', 'amount': 100})
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.data)

    def test_quote_exchange_rate_missing_params(self):
        response = self.client.get(self.url, {'from_currency': 'USD'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], "Please provide 'from_currency' and 'to_currency'.")

    def test_quote_exchange_rate_failure_from_api(self):
        response = self.client.get(self.url, {'from_currency': 'INVALID', 'to_currency': 'EUR'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error'], "Failed to fetch exchange rate.")


class ExchangeCurrencyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('exchange_currency')
        self.user = User.objects.create(name="Test User", daily_limit=1000.00, used_limit=0.00)

    def test_exchange_currency_success(self):
        response = self.client.post(self.url, {
            'user_id': self.user.id,
            'from_currency': 'USD',
            'to_currency': 'EUR',
            'amount': 5
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('transaction_id', response.data)
        self.assertIn('converted_amount', response.data)

    def test_exchange_currency_exceeds_limit(self):
        self.user.used_limit = 990.00
        self.user.save()
        response = self.client.post(self.url, {
            'user_id': self.user.id,
            'from_currency': 'USD',
            'to_currency': 'EUR',
            'amount': 20
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], "Daily limit exceeded.")

    def test_exchange_currency_failure_from_api(self):
        response = self.client.post(self.url, {
            'user_id': self.user.id,
            'from_currency': 'INVALID',
            'to_currency': 'EUR',
            'amount': 10
        })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error'], "Failed to complete transaction.")


class ViewTransactionsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('view_transactions')  # Asegúrate de que esta URL esté definida
        self.user = User.objects.create(name="Test User", daily_limit=1000.00)

        # Crear transacción con fecha actual (hoy) - con zona horaria
        self.tx1 = ExchangeTransaction.objects.create(
            user=self.user,
            from_currency="USD",
            to_currency="EUR",
            amount=10.00,
            result=9.00,
            exchange_rate=0.9,
            created_at=timezone.now()  # Fecha actual (aware)
        )

        # Crear transacción con fecha en el pasado (ayer) - con zona horaria
        self.tx2 = ExchangeTransaction.objects.create(
            user=self.user,
            from_currency="EUR",
            to_currency="USD",
            amount=15.00,
            result=16.50,
            exchange_rate=1.1,
            created_at=timezone.now() - timedelta(days=1)  # Ayer (aware)
        )

    def test_view_transactions_for_user(self):
        # Asegúrate de que el usuario tiene transacciones
        response = self.client.get(self.url, {'user_id': self.user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # Deberían ser 2 transacciones (de hoy y ayer)


    def test_view_transactions_with_invalid_date_range(self):
        # Rango de fechas inválido (de ayer a mañana)
        today = timezone.now().date()
        from_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        to_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client.get(self.url, {'user_id': self.user.id, 'from_date': from_date, 'to_date': to_date})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # Debería devolver 2 transacciones (de ayer y hoy)

    def test_view_transactions_no_transactions_in_date_range(self):
        # Filtramos por un rango de fechas en el que no hay transacciones
        today = timezone.now().date()
        from_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
        to_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')

        response = self.client.get(self.url, {'user_id': self.user.id, 'from_date': from_date, 'to_date': to_date})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)  # No debe devolver ninguna transacción
