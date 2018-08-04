import requests
import json
import dateutil.parser
import pytz
import datetime

def json_in_datetime(json):
    return dateutil.parser.parse(json["created_at"])
def json_in_print_text(json):
    try:
        title=json[u"repo"][u"name"]
        cm_msg=json[u"payload"][u"commits"][0][u"message"]
    except KeyError as e:
        title=""
        cm_msg=""
        print(e)
    return title,cm_msg

dt_now = datetime.datetime.now()
today_start=pytz.utc.localize(datetime.datetime(dt_now.year, dt_now.month, dt_now.day - 3, 0, 0, 0))

url=u"https://api.github.com/users/wasuken/events"
js_text=requests.get(url).text
data = json.loads(js_text)
result = [x for x in data if json_in_datetime(x) > today_start]
for x in result:
    print(json_in_print_text(x)[0])
