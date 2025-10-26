def convert_transaction_to_dict(transaction):
    return {
        "pk": str(transaction.id),
        "model": "payment.transaction",
        "fields": {
            "total_price": float(transaction.total_price),
            "amount_paid": float(transaction.amount_paid),
            "amount_due": float(transaction.amount_due),
            "payment_status": transaction.payment_status,
            "date": transaction.date.isoformat(),
            "updated_at": transaction.updated_at.isoformat(),
            "is_complete": transaction.is_complete,
            "entries": [{
                "id": e.product.id,
                "name": e.product.product_name,
                "amount": e.amount,
                "price": e.price,
            } for e in transaction.entries.all()]
        }
    } 
