import datetime

from basedata import HomeAssistantData, GoogleSheets, Util


def sync_weight():
    config_file = "weight.yaml"
    google = GoogleSheets(config_file)
    cells = google.get_cells()
    local_time = Util.str_to_datetime(cells[-1][0])

    ha_data = HomeAssistantData(config_file)
    new_items = ha_data.get_history(Util.local_to_utc(local_time + datetime.timedelta(seconds=1)),
                                    Util.local_to_utc(datetime.datetime.now()))
    rows = [[datetime.datetime.strftime(Util.utc_to_local(datetime.datetime.fromisoformat(item['last_changed'])),
                                        Util.get_date_format()), item['state']] for item in new_items[0]
            if item.get('attributes') is None]
    if len(rows) > 0:
        google.update_sheet(rows)


if __name__ == '__main__':
    sync_weight()