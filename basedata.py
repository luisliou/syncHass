import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import requests
import yaml
from datetime import datetime
import pytz


class Util:
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def get_date_format():
        return Util.DATE_FORMAT
    @staticmethod
    def str_to_datetime(dt):
        return datetime.strptime(dt, Util.DATE_FORMAT)

    @staticmethod
    def set_tz(dt, tz_name):
        local_tz = pytz.timezone(tz_name)
        return local_tz.localize(dt)

    @staticmethod
    def utc_to_local(utc_str, tz_name=None):
        if isinstance(utc_str, datetime):
            dt_utc = utc_str
        else:
            dt_utc = datetime.strptime(utc_str, Util.DATE_FORMAT)
        if tz_name is None:
            local_tz = pytz.timezone(pytz.country_timezones['se'][0])
        else:
            local_tz = pytz.timezone(tz_name)
        if dt_utc.tzinfo is None:
            dt_utc = pytz.timezone('UTC').localize(dt_utc)
        dt_local = dt_utc.astimezone(local_tz)
        return dt_local

    @staticmethod
    def local_to_utc(local_time_str, tz_name=None):
        if isinstance(local_time_str, datetime):
            local_time = local_time_str
        else:
            local_time = datetime.strptime(local_time_str, Util.DATE_FORMAT)
        if tz_name is not None:
            tz = pytz.timezone(tz_name)
            local_time = tz.localize(local_time)
        utc_time = local_time.astimezone(pytz.timezone("UTC"))
        return utc_time
    #
    # @staticmethod
    # def get_min_max_greater_than_zero(json_array):
    #     new_list = [x for x in json_array[0] if float(x['state']) > 0]
    #     max_item = max(new_list, key=lambda t: float(t['state']))
    #     min_item = min(new_list, key=lambda t: float(t['state']))
    #     start_time = Util.utc_to_local(min_item['last_changed'])
    #     end_time = Util.utc_to_local(max_item['last_changed'])
    #     return start_time, end_time, max_item['state']


class BaseConfig:
    @staticmethod
    def load_config(section, config_file):
        with open(config_file, "r") as f:
            return yaml.safe_load(f)[section]


class HomeAssistantData(BaseConfig):
    def __init__(self, config_file):
        config = BaseConfig.load_config("home_assistant", config_file=config_file)
        self.base_url = config.get("base_url")
        self.access_token = config.get("api")
        self.entity = config.get("entity")

    def get_states(self, entity):
        url = self.base_url + "/api/states/" + entity
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "content-type": "application/json"
        }

        response = requests.get(url, headers=headers)
        return response.json()["state"]

    def get_history(self, start_time, end_time):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }
        params = {
            "filter_entity_id": self.entity,
            "end_time": str(end_time),
            "minimal_response": ""
        }
        url = f"{self.base_url}/api/history/period/{start_time}"
        response = requests.get(url, headers=headers, params=params)
        response_json = response.json()
        return response_json


class GoogleSheets(BaseConfig):
    def __init__(self, config_file="grid.yaml"):
        config = BaseConfig.load_config("google_sheet", config_file=config_file)
        self.spreadsheet_id = config.get("spreadsheet_id")
        self.range_name = config.get("range_name")
        self.scopes = config.get("scopes")
        self.credentials_path = config.get("credentials_path")
        self.token_file = config.get("token_file")
        self.credentials_file = config.get("credentials_file")
        self.service = self.authenticate()

    def authenticate(self):
        token = f"{self.credentials_path}{self.token_file}"
        if os.path.exists(token):
            creds = Credentials.from_authorized_user_file(token, self.scopes)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                f"{self.credentials_path}{self.credentials_file}", self.scopes)
            creds = flow.run_local_server(port=0)

        return build('sheets', 'v4', credentials=creds)

    def update_sheet(self, rows):
        try:
            sheets = self.service.spreadsheets()
            result = sheets.values().append(spreadsheetId=self.spreadsheet_id,
                                            range=self.range_name,
                                            body={
                                                "majorDimension": "ROWS",
                                                "values": rows
                                            },
                                            valueInputOption="USER_ENTERED"
                                            ).execute()
            print(result)
        except ValueError:
            print("no data, skipped!")
            return -1

    def get_cells(self):
        sheets = self.service.spreadsheets()
        result = sheets.values().get(spreadsheetId=self.spreadsheet_id,
                                     range=self.range_name).execute()
        values = result.get('values', [])
        return values
