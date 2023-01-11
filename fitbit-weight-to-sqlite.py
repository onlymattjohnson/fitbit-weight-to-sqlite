from dotenv import load_dotenv
import os, requests

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

def is_token_valid(token):
    url = 'https://api.fitbit.com/1.1/oauth2/introspect'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {'token': f'{token}'}

    r = requests.post(url, data=data, headers=headers).json()
    
    if 'active' in r:
        return r['active']
    else:
        return r['success']

if __name__ == '__main__':
    # check if existing token is valid
    if is_token_valid(ACCESS_TOKEN):
        print("Token is valid. Let's goooooooooo")
    else:
        print("Token is NOT valid. Need to get a new token...")
