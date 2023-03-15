# ---------- START: api_data.py ----------
import requests
import json
import bearerCache as b
import get_config as cred


def get_data():
    url = "https://external.xolta.com/api/GetDataSummary"
    params = {
        "DeviceId": cred.api_deviceid,
        "SiteId": cred.api_siteid,
        "last": "3000",
        "IsBlob": "false",
        "CalculateConsumptionNeeded": "false",
        "resolutionMin": "10",
        "fromDateTime": "2023-02-16"
    }
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + b.get_auth_with_renewal()
    }

    response = requests.get(url, params=params, headers=headers)
    data = json.loads(response.text)
    # print(data)
    return data["telemetry"]

# ---------- END: api_data.py ----------

# ---------- START: bearerCache.py ----------
import hashlib
import json
import os
import time
from functools import cache
import xolta_get_auth
import get_config as cred


@cache
def get_auth():
    # check if the token is already cached and has not expired

    input_data = {'username': cred.api_username, 'password': cred.api_password}
    cache_key = hashlib.sha256(json.dumps(input_data).encode()).hexdigest()
    if os.path.exists(f"{cache_key}.txt"):
        with open(f"{cache_key}.txt", "r") as f:
            cached_token = json.load(f)
            print("cached token found!")
        if time.time() < cached_token['expires_at']:
            print("reusing cached token")
            return cached_token['access_token']

    # generate a new token
    print("Generating new token!")
    myXoltaAuth = xolta_get_auth.XoltaBattAuthenticator()
    token = myXoltaAuth.do_login(input_data)

    # cache the token and its expiration time
    expires_at = time.time() + 2 * 60 * 60  # 2 hours
    cached_token = {
        'access_token': token['access_token'], 'expires_at': expires_at}
    with open(f"{cache_key}.txt", "w") as f:
        json.dump(cached_token, f)

    return cached_token['access_token']


def get_auth_with_renewal():
    # check if the token is still valid or has expired
    input_data = {'username': cred.api_username, 'password': cred.api_password}
    cache_key = hashlib.sha256(json.dumps(input_data).encode()).hexdigest()
    if os.path.exists(f"{cache_key}.txt"):
        with open(f"{cache_key}.txt", "r") as f:
            cached_token = json.load(f)
        if time.time() < cached_token['expires_at']:
            return cached_token['access_token']
        else:
            # token has expired, delete the cached token file
            os.remove(f"{cache_key}.txt")

    # generate a new token and cache it
    access_token = get_auth()
    return access_token

# ---------- END: bearerCache.py ----------

# ---------- START: data_formatting.py ----------
import pytz
from datetime import datetime
import pandas as pd
import datapunkter


def format_data(telemetry_data, datatype):
    x = []
    y = []
    for telemetry in telemetry_data:
        utc_end_time = telemetry["utcEndTime"]
        meter_kwh = telemetry[datatype]
        # print(meter_kwh, utc_end_time)
        if meter_kwh is not None:
            # Convert UTC End Time to datetime object
            utc_end_time = datetime.strptime(
                utc_end_time, "%Y-%m-%dT%H:%M:%SZ")
            utc_end_time = pytz.utc.localize(utc_end_time)
            dk_timezone = pytz.timezone('Europe/Copenhagen')
            dk_end_time = utc_end_time.astimezone(dk_timezone)
            x.append(dk_end_time)
            y.append(meter_kwh)

    # Create a Pandas dataframe with the telemetry data
    df = pd.DataFrame({"x": x, "KWH": y})

    # Add a 'date' column to the dataframe
    df['date'] = df['x'].dt.date
    df['time'] = df['x'].dt.time

    return df

# ---------- END: data_formatting.py ----------

# ---------- START: datapunkter.py ----------
TELEMETRY_FIELDS = {
    2: {"name": "meterPvActivePowerAggAvgSiteSingle", "human_text": "Solcelle produktion"},
    3: {"name": "meterGridActivePowerAggAvgSiteSingle", "human_text": "ELnet forbrug"},
    5: {"name": "bmsSocRawArrayCloudTrimmedAggAvgSiteAvg", "human_text": "Batteri status"},
}


def get_telemetry_field_name(human_text):
    for telemetry_field in TELEMETRY_FIELDS.values():
        if telemetry_field['human_text'] == human_text:
            return telemetry_field['name']
    return None


def get_human_text_from_name(name):
    for key, value in TELEMETRY_FIELDS.items():
        if value['name'] == name:
            return value['human_text']
    return None

# ---------- END: datapunkter.py ----------

# ---------- START: get_config.py ----------
# make a file
#
# C:\Users\rasmu\api_credentials_xolta.ini
#
# and enter data like this :
#
#
# [api_credentials]
# username = <email>
# password = <password>

# [api_xolta_id]
# device-id = <id>
# site-id = <id>
#
import configparser

# change the location to your own
config_file_path = r'C:\Users\rasmu\api_credentials_xolta.ini'

config = configparser.ConfigParser()
config.read(config_file_path)

api_username = config.get('api_credentials', 'username')
api_password = config.get('api_credentials', 'password')

api_deviceid = config.get('api_xolta_id', 'device-id')
api_siteid = config.get('api_xolta_id', 'site-id')

# ---------- END: get_config.py ----------

# ---------- START: plot_data.py ----------
from matplotlib import cm
import matplotlib.pyplot as plt
import pytz
import numpy as np
from datetime import date, datetime
import pandas as pd


def add_lines(df, color, label, ax, dk_start_time, linewidth):
    df['datetime'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
    df['datetime'] = df['datetime'].apply(lambda t: datetime.combine(
        date.today(), t).replace(tzinfo=pytz.timezone('Europe/Copenhagen')))
    df['x'] = (df['datetime'] - dk_start_time).dt.total_seconds()
    ax.plot(df['x'], df['KWH'], label=label, linewidth=linewidth, color=color)


def plot_data(df, title):

    avg_kwh_df = df.groupby('time')['KWH'].mean().reset_index()
    # Determine the current date
    current_date = datetime.now().date()

    # Calculate the number of days since each date in the data
    df['date'] = df['x'].dt.date
    df['days_since_today'] = df['date'].apply(
        lambda x: (current_date - x).days)

    # Define a colormap
    cmap = cm.get_cmap('Blues')

    fig, ax = plt.subplots()

    for i, (date, date_data) in enumerate(df.groupby('date')):
        start_time = datetime.combine(date, datetime.min.time())
        dk_timezone = pytz.timezone('Europe/Copenhagen')
        dk_start_time = dk_timezone.localize(start_time)
        filtered_data = date_data.copy()
        filtered_data['x'] = (filtered_data['x'] -
                              dk_start_time).dt.total_seconds()

        start_time = 0

        x_max = 86400
        # Update x-axis ticks and labels
        x_ticks = np.linspace(start_time, x_max)
        ax.set_xticks(x_ticks)
        x_tick_labels = pd.to_datetime(x_ticks, unit='s').strftime('%H:%M')
        ax.set_xticklabels(x_tick_labels)

        # Determine the color based on the days_since_today value
        color = cmap(i / (len(df.groupby('date')) - 1))

        ax.plot(filtered_data['x'], filtered_data['KWH'],
                alpha=1, label=date.strftime("%Y-%m-%d"), color=color, linewidth=2)

    add_lines(avg_kwh_df, 'black', 'Avg. KWH', ax, dk_start_time, 6)

    # print(df)
    plt.xlabel("Klokken")
    plt.ylabel("KwP")
    plt.title(title + " pr. dag")
    plt.legend()

# ---------- END: plot_data.py ----------

# ---------- START: stack_days_one_color.py ----------
import matplotlib.pyplot as plt
import api_data as apidata
import data_formatting as formatdata
import plot_data as plotdata
import datapunkter


data_telemetry = apidata.get_data()

for i, field in datapunkter.TELEMETRY_FIELDS.items():
    print(field)
    name = field["name"]
    human_text = field["human_text"]
    df = formatdata.format_data(data_telemetry, name)
    plotdata.plot_data(df, human_text)


plt.show()

# ---------- END: stack_days_one_color.py ----------

# ---------- START: xolta_get_auth.py ----------
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire.utils import decode
import time
import datetime
import json

class XoltaBattAuthenticator():

    def log(self, msg):
        print(msg)


    def do_login(self, input_data):
        timeout = 10

        start_time = time.perf_counter()
        auth_response = {}

        try:
            self.log("Xolta: requesting site")
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            browser = webdriver.Chrome('chromedriver', options=chrome_options)

            try:
                self.log("Start Request")
                browser.get('https://app.xolta.com/')
                #time.sleep(timeout)

                self.log("Login form")

                email_field = WebDriverWait(browser, timeout).until(lambda d: d.find_element(By.ID, 'email'))
                email_field.clear()
                email_field.send_keys(input_data['username'])
                pswd_field = browser.find_element(By.ID, 'password')
                pswd_field.clear()
                pswd_field.send_keys(input_data['password'])

                # this doesn't always work, so wait an extra ½ second
                submitButton = WebDriverWait(browser, timeout).until(EC.element_to_be_clickable((By.ID, 'next')) )
                time.sleep(0.5)
                submitButton.click()

                # check if username/password is correct
                submitRequest = browser.wait_for_request('B2C_1_sisu/SelfAsserted', timeout)
                submitResponse = submitRequest.response
                body = decode(submitResponse.body, submitResponse.headers.get('Content-Encoding', 'identity'))
                body = body.decode('utf-8')
                data = json.loads(body)

                # copy login status and any messages to result
                auth_response.update(data)

                if data["status"] == '200':
                    # login successful. Wait for token...
                    tokenRequest = browser.wait_for_request('b2c_1_sisu/oauth2/v2.0/token', timeout)
                    tokenResponse = tokenRequest.response
                    body = decode(tokenResponse.body, tokenResponse.headers.get('Content-Encoding', 'identity'))
                    body = body.decode('utf-8')
                    data = json.loads(body)

                    auth_response.update({
                        "access_token": data['access_token'],
                        "refresh_token": data['refresh_token']
                    })

                browser.quit()
                self.log("Browser closed")

            except Exception as e:
                browser.quit()
                raise
        except Exception as e:
            self.log("XoltaBattAuthenticator Error: " + str(e))
            auth_response.update({
                "status": '500',
                "message": str(e)
            })

        auth_response.update({
            "duration": time.perf_counter() - start_time
        })

        self.log("Return: " + str(auth_response))
        return auth_response

# ---------- END: xolta_get_auth.py ----------

