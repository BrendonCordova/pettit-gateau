import mercadopago
from decouple import config

class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(config('MP_ACCESS_TOKEN'))

    def create_payment_preference(self, order, items_list):

        items = []
        for item in items_list:
            items.append({
                'title': f'{item.sku.product.name} - {item.sku.volume_ml}ml',
                'quantity': item.quantity,
                'unit_price': float(item.sku.price),
            })

        success_url = f'http://localhost:8000/pedidos/sucesso/{order.id}/'

        preference_data = {
            'items': items,
            'external_reference': str(order.id),
            'back_urls': {
                "success": success_url,
                "failure": "http://127.0.0.1:8000/carrinho/",
                "pending": "http://127.0.0.1:8000/pedidos/pendente/",
            },
            # 'auto_return': 'approved',
        }

        print("==== JSON ENVIADO PARA O MERCADO PAGO ====")
        print(preference_data)

        preference_response = self.sdk.preference().create(preference_data)

        if 'response' not in preference_response or 'sandbox_init_point' not in preference_response['response']:
            raise Exception(f"Erro Mercado Pago: {preference_response}")

        return preference_response['response']