import requests
import xml.etree.ElementTree as ET

class CorreiosService:
    '''
    Service class responsible for handling freight calculations.
    Integrates with ViaCEP for address validation and provides 
    dynamic shipping rates based on regional rules.
    '''
    def __init__(self, cep_origem='88790000'):
        '''Initializes the service with the store's origin ZIP code.'''
        self.cep_origem = cep_origem.replace('-', '')

    def calcular_frete(self, cep_destino, peso=1):
        '''
        Smart Freight Simulator.
        Ensures 100% uptime across the portfolio.
        Pricing logic focused on goods dispatch originating from Laguna, Santa Catarina, Brazil.
        '''
        cep = cep_destino.replace('-', '').strip()
        resultados = []

        if len(cep) != 8 or not cep.isdigit() or len(set(cep)) == 1:
            return {'error': 'Por favor, insira um CEP válido.'}

        try:
            viacep_url = f'https://viacep.com.br/ws/{cep}/json/'
            response = requests.get(viacep_url, timeout=3)
            data = response.json()
            
            if data.get('erro'):
                return {'error': 'Este CEP não consta na base dos Correios.'}
        except Exception:
            pass

        primeiro_digito = int(cep[0])

        if primeiro_digito in [8, 9]:
            preco_pac = 12.90 + (peso * 2)
            dias_pac = 3
            preco_sedex = 19.50 + (peso * 3)
            dias_sedex = 1
            
        elif primeiro_digito in [0, 1, 2, 3]:
            preco_pac = 24.50 + (peso * 3)
            dias_pac = 6
            preco_sedex = 38.90 + (peso * 4)
            dias_sedex = 3
            
        else:
            preco_pac = 38.90 + (peso * 4)
            dias_pac = 10
            preco_sedex = 68.50 + (peso * 6)
            dias_sedex = 5

        resultados.append({'name': 'PAC', 'price': f"{preco_pac:.2f}", 'days': dias_pac})
        resultados.append({'name': 'SEDEX', 'price': f"{preco_sedex:.2f}", 'days': dias_sedex})
            
        return resultados