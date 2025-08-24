import re
from typing import Dict
import requests
import base64

from mediaflow_proxy.extractors.base import BaseExtractor


def login_to_site(url, password):
    """Effettua il login al sito con la password fornita"""
    try:
        session = requests.Session()
        response = session.get(url)  # Prima richiesta per ottenere eventuali cookie
        response.raise_for_status()
        # Cerca il form di login e invia la password
        # Nota: questa parte potrebbe richiedere adattamenti in base al funzionamento effettivo del form
        login_data = {
            'password': password
        }
        response = session.post(url, data=login_data)  # Assumiamo che il form faccia POST alla stessa URL
        response.raise_for_status()
        # Verifica se il login è riuscito (controlla se siamo ancora nella pagina di login)
        if 'INSERIRE PASSWORD' in response.text:
            print('Login fallito. Password errata o form non trovato.')
            return None
        print('Login effettuato con successo!')
        return session
    except Exception as e:
        print(f'Errore durante il login: {e}')
        return None


class TestExtractor(BaseExtractor):
    async def extract(self, url: str, **kwargs) -> Dict[str, str]:

        session = login_to_site('https://thisnot.business', '2025')
        response = session.get(url).text
        matches = re.search(r'pages/player.html#(http.+?)[&?]+ck=([^"&]+)', response)
        if matches:
            mpd_url = matches[1]
            base64key = matches[2].replace('%3D', '=')
        else:
            print('\nNo MPD/keys found for:', url)

        keys = base64.b64decode(base64key + '=' * (-len(base64key) % 4)).decode('utf-8').replace(';', ',')

        return {
            "destination_url": mpd_url,
            "request_headers": self.base_headers,
            "mediaflow_endpoint": "mpd_manifest_proxy",
            "query_params": {
                "key_id": keys.split(':')[0],
                "key": keys.split(':', 1)[1],
            },
        }
