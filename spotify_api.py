
import base64
import requests
import logging
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate():
    try:
        client_creds = f'{CLIENT_ID}:{CLIENT_SECRET}'
        client_creds_b64 = base64.b64encode(client_creds.encode())

        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "client_credentials"
        }
        headers = {
            "Authorization": f"Basic {client_creds_b64.decode()}"
        }

        req = requests.post(url, data=data, headers=headers)
        req.raise_for_status()
        token_response_data = req.json()
        access_token = token_response_data['access_token']
        logger.info("Successfully authenticated with Spotify API")
        return access_token
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during authentication: {e}")
        return None

def get_recommendations(access_token):
    try:
        url = "https://api.spotify.com/v1/recommendations"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        data = urlencode({
            "seed_genres": "r-n-b,hip-hop"
        })
        res = requests.get(f'{url}?{data}', headers=headers)
        res.raise_for_status()
        json = res.json()
        response = []
        for album in json['tracks']:
            name = album['name']
            href = album['href']
            duration_ms = album['duration_ms']
            response.append([name, href, duration_ms])
        logger.info("Successfully fetched recommendations from Spotify API")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching recommendations: {e}")
        return []
