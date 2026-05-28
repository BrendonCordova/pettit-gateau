import mercadopago
from decouple import config

class MercadoPagoService:
    '''
    Service class responsible for interacting with the Mercado Pago API.
    Handles the authentication and the creation of payment preferences.
    '''
    def __init__(self):
        '''Initializes the Mercado Pago SDK using the access token from environment variables.'''
        self.sdk = mercadopago.SDK(config('MP_ACCESS_TOKEN'))

    def create_payment_preference(self, order, items_list):
        '''
        Builds and registers a payment preference payload with Mercado Pago.
        Configures return URLs (success, pending, failure) and the webhook notification endpoint.

        Args:
            order (Order): The order instance triggering the payment.
            items_list (QuerySet): A list of cart items to be formatted for the gateway.

        Returns:
            dict: The Mercado Pago response dictionary containing the 'sandbox_init_point' URL.
            
        Raises:
            Exception: If the Mercado Pago API fails to return a valid initialization URL.
        '''
        items = []
        for item in items_list:
            items.append({
                'title': f'{item.sku.product.name} - {item.sku.volume_ml}ml',
                'quantity': item.quantity,
                'unit_price': float(item.sku.price),
            })

        success_url = f'http://localhost:8000/pedidos/sucesso/{order.id}/'

        base_url = config('WEBHOOK_BASE_URL', default='http://localhost:8000')
        webhook_url = f'{base_url}/pedidos/webhook/mercado-pago/'

        preference_data = {
            'items': items,
            'external_reference': str(order.id),
            'back_urls': {
                "success": success_url,
                "failure": "http://127.0.0.1:8000/carrinho/",
                "pending": "http://127.0.0.1:8000/pedidos/pendente/",
            },
            # 'auto_return': 'approved',
            'notification_url': webhook_url,
        }

        print("==== JSON ENVIADO PARA O MERCADO PAGO ====")
        print(preference_data)

        preference_response = self.sdk.preference().create(preference_data)

        if 'response' not in preference_response or 'sandbox_init_point' not in preference_response['response']:
            raise Exception(f"Erro Mercado Pago: {preference_response}")

        return preference_response['response']