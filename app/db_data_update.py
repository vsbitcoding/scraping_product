import json
from datetime import datetime
import logging
from .models import Products
import os
import concurrent.futures
import time

logging.basicConfig(filename="/home/ubuntu/project/app/cron.log", level=logging.INFO)
current = datetime.now()
today_date = str(f"{current.month}/{current.year}")


# def db_data_update_handle():
#     logging.info(f'{current} Cron job Started db_data_update_handle')   
#     dir_files = os.listdir("/home/ubuntu/project/app/cron_json")
#     logging.info(f"{dir_files} dir_files---------------------")
    
#     # data_json_file = open("/home/ubuntu/Documents/store_django/project/updated_listing.json")
#     for files in dir_files:
#         with open(f'/home/ubuntu/project/app/cron_json/{files}') as f:
#             josn_data = json.load(f)
#         logging.info(f"{type(josn_data)} length data---------------------")
#         logging.info(f"{len(josn_data)} length data---------------------")
#         for row in josn_data:
#             previous_data = ""
#             is_products = Products.objects.filter(listing_id=row["listing_id"], date=today_date)
#             if is_products.exists():
            
#                 previous_data = (
#                         is_products.first().quantity_remaining
#                         if is_products.first().quantity_remaining
#                         else row['quantity_remaining']
#                     )
#                 previous_sold_product = is_products.first().sold_quantity
#                 sold = int(previous_data) - row['quantity_remaining']
#                 total_sold_quantity = previous_sold_product + abs(sold)
#                 to_be_update = {"buy_price": row["buy_price"], "available_to_buy": row['quantity_remaining'], "quantity_remaining": row['quantity_remaining'], "sold_quantity" : total_sold_quantity}
#                 is_products.update(**to_be_update)
#             else:
#                 Products.objects.create(
#                     sku_id=row["sku_id"],
#                     store_name=row["member_name"],
#                     listing_id=row["listing_id"],
#                     date=today_date,
#                     title=row["title"],
#                     buy_price=row["buy_price"],
#                     category_path=row["category_path"],
#                     image_url=row['img_url'],
#                     photo_id="" if row["photo_id"] == None else row["photo_id"],
#                     available_to_buy=row['quantity_remaining'],
#                     quantity_remaining=row['quantity_remaining'],
#                 )
#         os.remove(f'/home/ubuntu/project/app/cron_json/{files}')
#         logging.info(f"function run successfully ................................>>>>>>>>>>>>>>>>>>>>>>>>>>>")

def db_data_update_handle():
    logging.info(f"{current} in listing_cron_scrap_data request function")
    
    # Load all JSON files in directory
    dir_path = "/home/ubuntu/project/app/cron_json"
    logging.info(f"os.listdir(dir_path)......................{os.listdir(dir_path)}")
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
    json_data = []
    for file in json_files:
        with open(os.path.join(dir_path, file)) as f:
            file_data = json.load(f)
            json_data.extend(file_data)
        os.remove(os.path.join(dir_path, file))  # Remove file after reading its contents

    # Use a thread pool to update/create products
    args = [(row, today_date) for row in json_data]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(update_or_create_product, args))

def update_or_create_product(args):
    row, today_date = args
    is_product = Products.objects.filter(listing_id=row["listing_id"], date=today_date).first()
    if is_product:
        previous_data = is_product.quantity_remaining or row['quantity_remaining']
        sold = int(previous_data) - row['quantity_remaining']
        total_sold_quantity = is_product.sold_quantity + abs(sold)
        is_product.buy_price = row["buy_price"]
        is_product.available_to_buy = row['quantity_remaining']
        is_product.quantity_remaining = row['quantity_remaining']
        is_product.sold_quantity = total_sold_quantity
        is_product.save()
    else:
        Products.objects.create(
            sku_id=row["sku_id"],
            store_name=row["member_name"],
            listing_id=row["listing_id"],
            date=today_date,
            title=row["title"],
            buy_price=row["buy_price"],
            category_path=row["category_path"],
            image_url=row['img_url'],
            photo_id="" if row["photo_id"] == None else row["photo_id"],
            available_to_buy=row['quantity_remaining'],
            quantity_remaining=row['quantity_remaining'],
        )
