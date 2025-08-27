import re
from typing import Dict
import requests
import base64
import json

from mediaflow_proxy.extractors.base import BaseExtractor


def login_to_site(url, password):
    """Login to site"""
    try:
        session = requests.Session()
        response = session.get(url)
        response.raise_for_status()
        login_data = {
            'password': password
        }
        response = session.post(url, data=login_data)
        response.raise_for_status()
        if 'INSERIRE PASSWORD' in response.text:
            print('Login failed.')
            return None
        print('Login successful!')
        return session
    except Exception as e:
        print(f'Error during login: {e}')
        return None


def dec(s):
    return base64.b64decode(s).decode()


class TestExtractor(BaseExtractor):
    async def extract(self, url: str, **kwargs) -> Dict[str, str]:
        session = login_to_site(dec("aHR0cHM6Ly90aGlzbm90LmJ1c2luZXNz"), dec("MjAyNQ=="))
        response = session.get(url).text
        matches = re.search(r'pages/player\.html#(http(?:(?![?&]ck=)[^"])+)(?:[?&]ck=([^"&]+))?', response)
        if matches:
            mpd_url = re.sub(dec('ZGNbYWJdLXJ3LWxpdmVkYXpuLmNkblwubmV0cncuaXQ='), dec('ZGNhLWNvLWxpdmUtZ2NyLmdjZG4uY28='), matches[1])
            if matches[2]:
                base64key = matches[2].replace('%3D', '=')
            else:
                base64key = None
        else:
            print('\nNo MPD found for:', url)

        data = {
            "destination_url": mpd_url,
            "request_headers": self.base_headers,
            "mediaflow_endpoint": dec('bXBkX21hbmlmZXN0X3Byb3h5')
        }

        if base64key:
            keys = base64.b64decode(base64key + '=' * (-len(base64key) % 4)).decode('utf-8').replace(';', ',')
            try:  # Unpack {"kid1":"key1", "kid2":"key2"} to "kid1:key1,kid2:key2"
                keys = ','.join(f'{kid}:{key}' for kid, key in json.loads(keys).items())
            except json.JSONDecodeError:
                pass
            data.update({
                "query_params": {
                    "key_id": keys.split(',')[0].split(':')[0],
                    "key": keys.split(',')[0].split(':')[1],
                }
            })

        return data
