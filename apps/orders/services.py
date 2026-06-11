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
        Generates the payload and creates a payment preference in Mercado Pago.
        Handles discounts by grouping items into a single transactional entry 
        to prevent floating-point rounding errors and negative values in the external API.
        '''
        items = []
        
        if order.discount_amount and order.discount_amount > 0:
            valor_produtos_com_desconto = float(order.total_price - order.shipping_price)
            items.append({
                'title': f'Pedido #{str(order.id)[:8]} - Pettit Gateau',
                'description': 'Produtos com cupom de desconto aplicado.',
                'quantity': 1,
                'unit_price': valor_produtos_com_desconto,
            })
        else:
            for item in items_list:
                preco_unitario = item.price if hasattr(item, 'price') else item.sku.price
                items.append({
                    'title': f'{item.sku.product.name} - {item.sku.volume_ml}ml',
                    'quantity': item.quantity,
                    'unit_price': float(preco_unitario),
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
            'notification_url': webhook_url,
        }

        if order.shipping_price and order.shipping_price > 0:
            preference_data['shipments'] = {
                'cost': float(order.shipping_price),
                'mode': 'not_specified'
            }

        print("==== JSON ENVIADO PARA O MERCADO PAGO ====")
        print(preference_data)

        preference_response = self.sdk.preference().create(preference_data)

        if 'response' not in preference_response or 'sandbox_init_point' not in preference_response['response']:
            raise Exception(f"Erro Mercado Pago: {preference_response}")

        return preference_response['response']