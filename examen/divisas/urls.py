from django.urls import path
from . import views

urlpatterns = [
    path('quote-exchange-rate/', views.quote_exchange_rate, name='quote_exchange_rate'),
    path('exchange-currency/', views.exchange_currency, name='exchange_currency'),
    path('view-transactions/', views.view_transactions, name='view_transactions'),
]
