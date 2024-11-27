from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    used_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class ExchangeTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    result = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
