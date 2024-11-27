import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import ExchangeTransaction, User
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from datetime import datetime

API_KEY = "54987|PkVT7oUVrjaBWmitnqQg"  # Considera mover esto a una variable de entorno para mayor seguridad

@api_view(['GET'])
def quote_exchange_rate(request):
    from_currency = request.query_params.get('from_currency')
    to_currency = request.query_params.get('to_currency')
    amount = request.query_params.get('amount', 1)
    
    if not from_currency or not to_currency:
        return Response({"error": "Please provide 'from_currency' and 'to_currency'."}, status=400)
    
    url = f"https://api.cambio.today/v1/quotes/{from_currency}/{to_currency}/json?quantity={amount}&key={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return Response(data)
    else:
        return Response({"error": "Failed to fetch exchange rate."}, status=500)

@api_view(['POST'])
@transaction.atomic
def exchange_currency(request):
    user_id = request.data.get('user_id')
    from_currency = request.data.get('from_currency')
    to_currency = request.data.get('to_currency')
    amount = Decimal(request.data.get('amount', 0))  # Convertimos amount a Decimal
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)
    
    # Convertimos user.used_limit y user.daily_limit a Decimal también
    if Decimal(user.used_limit) + amount > Decimal(user.daily_limit):
        return Response({"error": "Daily limit exceeded."}, status=400)
    
    url = f"https://api.cambio.today/v1/quotes/{from_currency}/{to_currency}/json?quantity={amount}&key={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        rate = Decimal(response.json()['result']['value'])  # Aseguramos que rate sea Decimal
        converted_amount = amount * rate
        
        # Guardar la transacción
        transaction = ExchangeTransaction.objects.create(
            user=user,
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            result=converted_amount,
            exchange_rate=rate
        )
        
        # Actualizamos el límite usado
        user.used_limit = Decimal(user.used_limit) + amount
        user.save()
        
        return Response({"transaction_id": transaction.id, "converted_amount": converted_amount})
    else:
        return Response({"error": "Failed to complete transaction."}, status=500)

@api_view(['GET'])
def view_transactions(request):
    user_id = request.query_params.get('user_id')
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date')
    
    # Convierte las fechas en objetos datetime si están presentes
    if from_date:
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    if to_date:
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

    # Traemos las transacciones filtradas por el user_id
    transactions = ExchangeTransaction.objects.filter(user_id=user_id)

    # Si las fechas están presentes, filtramos por ellas
    if from_date and to_date:
        transactions = transactions.filter(created_at__date__range=[from_date, to_date])
    elif from_date:
        transactions = transactions.filter(created_at__date__gte=from_date)
    elif to_date:
        transactions = transactions.filter(created_at__date__lte=to_date)

    # Preparamos la respuesta con los datos
    data = [
        {
            "id": tx.id,
            "from_currency": tx.from_currency,
            "to_currency": tx.to_currency,
            "amount": tx.amount,
            "result": tx.result,
            "exchange_rate": tx.exchange_rate,
            "created_at": tx.created_at.isoformat()  # Usamos isoformat para representar la fecha en formato ISO
        } for tx in transactions
    ]
    return Response(data)
