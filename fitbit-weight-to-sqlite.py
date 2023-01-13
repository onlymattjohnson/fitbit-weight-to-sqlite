from base64 import b64encode
from datetime import date, datetime
from dotenv import load_dotenv
import json, os, requests, sqlite3

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
DATABASE_LOCATION = os.getenv("DATABASE_LOCATION")

def log_output(t):
    """
    Produces a log output to stdout
    """
    d = datetime.now()
    print(f'{d} : {t}')

def check_if_row_exists(conn, weight_log):
    """
    Check if row already exists before updating
    """
    sql = f'''
        select 1 from weight
        where 
            date = '{weight_log['date']}'
            and weight = {weight_log['weight']} 
    '''
    cur = conn.cursor()
    cur.execute(sql)

    result = len(cur.fetchall()) >= 1
    if result:
        log_output(f'Data for {weight_log["date"]} already exists, skipping insert.')

    return result

def create_db_connection(db):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db)
    except Error as e:
        log_output(e)
        sys.exit()

    return conn

def encode_credentials():
    base_string = f'{CLIENT_ID}:{CLIENT_SECRET}'
    base_bytes = base_string.encode('ascii')
    encode_string = b64encode(base_bytes)
    return encode_string.decode('ascii')

def get_new_tokens():
    global ACCESS_TOKEN
    global REFRESH_TOKEN

    url = 'https://api.fitbit.com/oauth2/token'
    
    client_key = encode_credentials()
    auth_header = f'Basic {client_key}'

    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }

    r = requests.post(url, data=payload, headers = headers)

    json_response = r.json()
    if 'errors' in json_response:
        log_output('Could not connect to Fitbit server.')
        for e in json_response['errors']:
            error_type = e['errorType']
            error_message = e['message']
            log_output(f'Error Type: {error_type}, Message: {error_message}')
    else:
        t1 = json_response['access_token']
        t2 = json_response['refresh_token']
        save_tokens(t1,t2)

        ACCESS_TOKEN = t1
        REFRESH_TOKEN = t2

def fetch_all_weight_logs():
    # Fetch the last 30 days of weight logs
    today = date.today()
    base_date = today.strftime('%Y-%m-%d')

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'accept-language': 'en_US'
    }

    url = f'https://api.fitbit.com/1/user/-/body/log/weight/date/{base_date}/30d.json'

    r = requests.get(url, headers=headers).json()['weight']

    return r

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

def save_tokens(t1, t2):
    with open('.env', 'r') as file:
        data = file.readlines()
    data[2] = f'ACCESS_TOKEN={t1}\n'
    data[3] = f'REFRESH_TOKEN={t2}\n'

    with open('.env', 'w') as file:
        file.writelines(data)

    log_output('Saved new access tokens to .env file')

def save_weight_log(weight_log, conn):
    """
    Save all weight logs into database
    """
    # Create a copy to work with
    weight_log = dict(weight_log)

    # Check if row already exists first
    if not check_if_row_exists(conn, weight_log):
    # SQL to work with
        sql = f'''
            INSERT INTO weight(date, time, external_id, external_source_name, device_name, weight)
            VALUES (
                '{weight_log['date']}', 
                '{weight_log['time']}',
                {weight_log['logId']},
                'Fitbit',
                '{weight_log['source']}',
                {weight_log['weight']} 
            ) 
        '''
        cur = c.cursor()
        cur.execute(sql)
        c.commit()

        return cur.lastrowid
    return -1

if __name__ == '__main__':
    # check if existing token is valid
    if is_token_valid(ACCESS_TOKEN):
        log_output("Fitbit Authentication Token is valid.")
    else:
        log_output("Fitbit Authentication Token is NOT valid. Fetching new tokens...")
        get_new_tokens()
    
    c = create_db_connection(DATABASE_LOCATION)

    w = fetch_all_weight_logs()
    for log in w:
        r = save_weight_log(log, c)
        if r != -1:
            print(f'Inserted new row for {log["date"]} - ROWID {r}')
