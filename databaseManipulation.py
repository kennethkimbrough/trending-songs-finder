import base64
import requests
import mysql.connector
from urllib.parse import urlencode

client_id = 'aeebc41231ae498d9c0ae4747e4077d9'
client_secret = '6d9184da4aea43b38b376c2cfefbca98'

def authenticate(client_id, client_secret):
    client_creds = f'{client_id}:{client_secret}'
    client_creds_b64 = base64.b64encode(client_creds.encode())

    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": f'client_credentials'
    }
    headers = {
        "Authorization": f"Basic {client_creds_b64.decode()}"
    }

    req = requests.post(url, data=data, headers=headers)
    token_response_data = req.json()
    access_token = token_response_data['access_token']
    return access_token

def get_recommendations(access_token):
    url = "https://api.spotify.com/v1/recommendations"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = urlencode({
        "seed_genres": "r-n-b,hip-hop"
    })
    res = requests.get(f'{url}?{data}', headers=headers)
    json = res.json()
    response = []
    for album in json['tracks']:
        name = album['name']
        href = album['href']
        duration_ms = album['duration_ms']
        response.append([name, href, duration_ms])
    return response

def save(data):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="dbspotify"
    )
    mycursor = mydb.cursor()
    if len(data) > 0:
        for row in data:
            sql = "INSERT INTO records (name, duration, url) VALUES (%s,%s,%s)"
            val = (row[0], row[1], row[2])
            mycursor.execute(sql, val)
        mydb.commit()
    
access_token = authenticate(client_id, client_secret)
data = get_recommendations(access_token)
save(data)
