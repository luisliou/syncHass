from datetime import datetime, timedelta

from basedata import HomeAssistantData, GoogleSheets

from basedata import Util


def get_daily_usage(date_value_dict, local_start_date, local_end_date, tz_name):
    max_value_dict = {}
    for item in date_value_dict:
        if item.get('state') is None or item.get('last_changed') is None:
            continue
        date = Util.utc_to_local(datetime.fromisoformat(item['last_changed']), tz_name=tz_name)
        if date < local_start_date or date > local_end_date:
            continue
        date = date.replace(second=59, minute=59, hour=23, microsecond=0)
        state = item['state']
        if date in max_value_dict:
            max_value_dict[date] = max(max_value_dict[date], state)
        else:
            max_value_dict[date] = state
    return max_value_dict


def sync_grid():
    tz_name = 'Asia/Shanghai'
    hass = HomeAssistantData(config_file="grid.yaml")
    google = GoogleSheets()
    cells = google.get_cells()
    local_start_date = datetime.fromisoformat(cells[-1][0])
    local_start_date = Util.set_tz(local_start_date + timedelta(seconds=1), tz_name)
    utc_start_date = Util.local_to_utc(local_start_date)
    local_end_date = Util.set_tz(datetime.now().replace(hour=23, minute=59, second=59, microsecond=0), tz_name)
    utc_end_date = Util.local_to_utc(local_end_date)
    date_value_dict = hass.get_history(utc_start_date, utc_end_date)[0]
    daily_usage_dict = get_daily_usage(date_value_dict, local_start_date, local_end_date, tz_name=tz_name)
    rows = [[dt.strftime('%Y-%m-%d %H:%M:%S'), value] for dt, value in daily_usage_dict.items()]
    google.update_sheet(rows)
    print(daily_usage_dict)


if __name__ == '__main__':
    sync_grid()
