import requests
import json
from .models import *
import logging
import datetime

date_time = datetime.datetime.now()

logging.basicConfig(filename="/home/ubuntu/project/app/cron.log", level=logging.INFO)


def cron_handle():
    # logger = logging.getLogger('cron_job')
    print("cron starded")
    stores = list(
        Store.objects.filter(action="active").values_list("store_id", flat=True)
    )
    for store in stores:
        print(f"{store} store cron")
        payload = json.dumps({"member_id": [store]})
        headers = {"Content-Type": "application/json"}
        requests.post(
            "http://localhost:5000/member_id_cron", data=payload, headers=headers
        )
    # logger.debug(f'{date_time} Cron job Started.')
    logging.info(f"{date_time} Cron job Started.")
