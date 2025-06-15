# type: ignore
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class BlizzardConfig:
    """Configuration for Blizzard API"""
    client_id: str
    client_secret: str
    region: str = 'us'
    timeout: int = 10
    max_retries: int = 3

def create_session(config):
    """Create a requests session with retry strategy"""
    retry_strategy = Retry(
        total=config.max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    return session

def get_access_token(config, session):
    """Get OAuth access token from Blizzard"""
    token_url = "https://oauth.battle.net/token"
    data = {'grant_type': 'client_credentials'}
    auth = (config.client_id, config.client_secret)

    response = session.post(token_url, data=data, auth=auth, timeout=config.timeout)
    response.raise_for_status()

    token_data = response.json()
    return {
        'access_token': token_data['access_token'],
        'expires_at': time.time() + token_data['expires_in']
    }

class BlizzardAPI:
    """Improved Blizzard API client with better separation of concerns"""

    def __init__(self, config):
        self.config = config
        self.session = create_session(config)
        self._token_info = None

    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if (not self._token_info or
            time.time() >= float(self._token_info['expires_at'])):
            self._token_info = get_access_token(self.config, self.session)

    def _make_request(self, method, url, params=None):
        """Make an authenticated request

        Returns:
            - requests.Response object for HEAD requests
            - Dict for all other request types (after JSON parsing)
        """
        self._ensure_valid_token()

        if self._token_info is None:
            raise RuntimeError("Access token is not available. Please authenticate first.")

        headers = {'Authorization': f'Bearer {self._token_info["access_token"]}'}

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            return response if method.upper() == 'HEAD' else response.json()

        except requests.exceptions.RequestException as e:
            print(e)
            raise  # Re-raise the exception after printing it

    def _build_url(self, endpoint):
        """Build full API URL"""
        return f"https://{self.config.region}.api.blizzard.com{endpoint}"

    def _static_params(self):
        """Common parameters for static data"""
        return {
            'namespace': f'static-{self.config.region}',
            'locale': 'en_US'
        }

    def _dynamic_params(self):
        """Common parameters for dynamic data"""
        return {
            'namespace': f'dynamic-{self.config.region}',
            'locale': 'en_US'
        }

    # Public API methods

    def is_commodities_updated(self, last_check):
        """Check if commodities data has been updated"""
        if last_check is None:
            return True

        url = self._build_url("/data/wow/auctions/commodities")
        response = self._make_request('HEAD', url, self._dynamic_params())

        last_modified = datetime.strptime(response.headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=timezone.utc)

        return last_modified > last_check


    def get_commodities(self):
        """Get auction house commodities"""
        url = self._build_url("/data/wow/auctions/commodities")
        response = self._make_request('GET', url, self._dynamic_params())
        return response

    def get_item(self, item_id):
        """Get item details by ID"""
        url = self._build_url(f"/data/wow/item/{item_id}")
        response = self._make_request('GET', url, self._static_params())
        return response

    def get_professions(self):
        """Get list of all professions"""
        url = self._build_url("/data/wow/profession/index")
        response = self._make_request('GET', url, self._static_params())
        return response['professions']

    def get_profession_info(self, profession_href):
        """Get skill tiers for a profession"""
        response = self._make_request('GET', profession_href, self._static_params())
        return response

    def get_skill_tier_details(self, skill_tier_href):
        """Get recipes for a skill tier"""
        response = self._make_request('GET', skill_tier_href, self._static_params())
        return response

    def get_recipe_info(self, recipe_href):
        """Get ingredients for a recipe"""
        response = self._make_request('GET', recipe_href, self._static_params())
        return response

def example_usage():
    config = BlizzardConfig(
        client_id="",
        client_secret="6CkDstcu395FBCnBz3Xf8zej3pKJ6if2",
        region="us"
    )

    api = BlizzardAPI(config)

    # Simple, clean usage
    professions = api.get_professions()

    print("professions:", professions)

example_usage()
