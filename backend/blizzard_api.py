from datetime import datetime, strptime, timezone
from typing import Dict, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from typing import Union

class BlizzardAPI:
    def __init__(self, client_id, client_secret, region='us'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.access_token = None
        self.token_time = None
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    
    def _make_request(self, method: str, url: str, params: Dict = None, data: Dict = None, auth: tuple = None) -> Dict:
        try:
            if not auth and (not self.access_token or time.time() > self.token_expiry):
                self.get_access_token()
            
            headers = {'Authorization': f'Bearer {self.access_token}'} if not auth else None
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                auth=auth,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            raise

    def get_access_token(self):
        """Get OAuth access token from Blizzard"""
        token_url = "https://oauth.battle.net/token"
        data = {'grant_type': 'client_credentials'}
        auth = (self.client_id, self.client_secret)
        
        token_data = self._make_request('POST', token_url, data=data, auth=auth)
        self.access_token = token_data['access_token']
        self.token_expiry = time.time() + token_data['expires_in']
        
    def is_commodities_updated(self, time: Union[datetime, None]) -> bool:
        """Check if the commodities data has been updated"""
        if time is None:
            return True
        
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        url = f"https://{self.region}.api.blizzard.com/data/wow/auctions/commodities"
        params = {
            'namespace': f'dynamic-{self.region}',
            'locale': 'en_US'
        }
        
        response = self._make_request('HEAD', url, params=params)
        
        last_modified = datetime.strptime(response.headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z')
        last_modified = last_modified.replace(tzinfo=timezone.utc)
        
        return last_modified > time
    
    def get_commodities(self):
        """Get auction house commodities if it has been modified since last check"""
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        url = f"https://{self.region}.api.blizzard.com/data/wow/auctions/commodities"
        params = {
            'namespace': f'dynamic-{self.region}',
            'locale': 'en_US'
        }
        
        return self._make_request('GET', url, params=params)
    
    def get_item(self, item_id):
        """Get item details by ID"""
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        item_url = f"https://{self.region}.api.blizzard.com/data/wow/item/{item_id}"
        params = {
            'namespace': f'static-{self.region}',
            'locale': 'en_US'
        }
        
        return self._make_request('GET', item_url, params=params)
        
    def get_professions(self) -> List[Dict]:
        """Get a list of all professions"""
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        prof_url = f"https://{self.region}.api.blizzard.com/data/wow/profession/index"
        params = {
            'namespace': f'static-{self.region}',
            'locale': 'en_US'
        }
        
        response = self._make_request('GET', prof_url, params=params)
        print("Professions retrieved")
        return response['professions']
        
    def get_profession_info(self, profession: Dict) -> List[Dict]:
        """Get skill tiers for a profession"""
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        prof_detail_url = profession['key']['href']
        params = {
            'namespace': f'static-{self.region}',
            'locale': 'en_US'
        }
        
        return self._make_request('GET', prof_detail_url, params=params)
    
    def get_skill_tier_details(self, skill_tier: Dict) -> List[Dict]:
        """Get recipes for a skill tier"""
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        tier_url = skill_tier['key']['href']
        params = {
            'namespace': f'static-{self.region}',
            'locale': 'en_US'
        }
        
        return self._make_request('GET', tier_url, params=params)
        
    def get_recipe_info(self, recipe: Dict) -> Dict:
        """Get ingredients for a recipe"""
        if not self.access_token or time.time() > self.token_expiry:
            self.get_access_token()
            
        recipe_url = recipe['key']['href']
        params = {
            'namespace': f'static-{self.region}',
            'locale': 'en_US'
        }
        
        return self._make_request('GET', recipe_url, params=params)
