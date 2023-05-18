import os
import csv
import time
import pytz
import json
import logging
import requests
import threading
from .models import *
from lxml import etree
from .forms import InputForm
from bs4 import BeautifulSoup
from datetime import datetime
from django.db.models import Sum
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, HttpResponse
from  .db_data_update import db_data_update_handle

logger = logging.getLogger(__name__)

current = datetime.now()
today_date = str(f"{current.month}/{current.year}")


# Create your views here.
@csrf_exempt
def index(request):
    form = InputForm()
    all_store = Store.objects.all()
    if request.method == "POST":
        store_url = request.POST.get("store_id")
        if "stores" in store_url:
            response = requests.request("GET", store_url)
            soup = BeautifulSoup(response.text, "html.parser")
            dom = etree.HTML(str(soup))
            store_id = dom.xpath('//input[@name="member"]')[0].get("value")
            store_name = store_url.split("/")[-1]
        else:
            response = requests.request("GET", store_url)
            soup = BeautifulSoup(response.text, "html.parser")
            dom = etree.HTML(str(soup))
            store_id = store_url.split("=")[-1]
            store_name = (
                dom.xpath(
                    '//a[@class="h-link-no-visited tm-member-profile-banner__title p-h1"]/text()'
                )[0]
                .strip()
                .split("(")[0]
                .strip()
            )

        try:
            Store.objects.get(store_id=store_id)
        except Store.DoesNotExist:
            Store.objects.create(store_id=store_id, store_name=store_name)

        return render(
            request,
            "home.html",
            {
                "form": form,
                "store": store_name,
                "store_id": store_id,
                "all_store": all_store,
            },
        )
    return render(request, "home.html", {"form": form, "all_store": all_store})

@csrf_exempt
def scrape_store(request, store_id):
    if request.method == "GET":
        payload = json.dumps({"member_id": [store_id]})
        headers = {"Content-Type": "application/json"}
        requests.post("http://0.0.0.0:5000/member_id", data=payload, headers=headers)
        return redirect("/")
    return HttpResponse({"Method Not Allowed"}, status=405)

@csrf_exempt
def button_action(request, store_id, action):
    store = Store.objects.get(store_id=store_id)
    store.action = action
    store.save()
    return redirect("/")


@csrf_exempt
def product_list(request):
    return render(request, "product.html")


logging.basicConfig(filename="/home/ubuntu/project/app/cron.log", level=logging.INFO)

@csrf_exempt
def cron_scrape_store(request, store_id):
    store = list(
        Store.objects.filter(action="active").values_list("store_id", flat=True)
    )
    payload = json.dumps({"member_id": store})
    headers = {"Content-Type": "application/json"}
    requests.post("http://0.0.0.0:5000/member_id_cron", data=payload, headers=headers)


logging.basicConfig(filename="/home/ubuntu/project/app/cron.log", level=logging.INFO)


@csrf_exempt
def cron_scrap_data(request):
    logging.info(f"{current} in cron_scrap_data request function")
    if request.method == "POST":
        data = json.loads(request.body)
        scraper_listing_ids = [listing["listing_id"] for listing in data]
        exclude_scraper_listing_id = list(Products.objects.filter(store_name = data[0]['member_name']).exclude(listing_id__in=scraper_listing_ids).values_list("listing_id", flat=True))
        logging.info(f"{len(exclude_scraper_listing_id)} length of exclude_scraper_listing_id+++++++++++++++++++")
        logging.info(f"{len(data)} length of request data")
        json_object = json.dumps(data)
        with open(f"/home/ubuntu/project/app/cron_json/{data[0]['member_id']}.json", "w") as outfile:
            outfile.write(json_object)
        logging.info(
            f" Before Initialize the list++++++++++++++++++++++++++++++++++"
        )
        payload = json.dumps({"listing_id": exclude_scraper_listing_id})
        headers = {"Content-Type": "application/json"}
        requests.post("http://localhost:5000/listing_id", data=payload, headers=headers)
        logging.info(
            f"{current} {len(exclude_scraper_listing_id)} listind_id_list sent for reqest function"
        )
        time.sleep(10)
        db_data_update_handle()
        return HttpResponse({"Data store successfully"}, status=200)
    return HttpResponse({"Method Not Allowed"}, status=405)


@csrf_exempt
def scrap_data(request):
    if request.method == "POST":
        logging.info(f'{current} in scrap_data request function')
        # Response data from scraper
        data = json.loads(request.body)
        
        # Scraper data listing ids list
        scraper_listing_ids = [listing["listing_id"] for listing in data]
        logging.info(f"{len(scraper_listing_ids)} length of scraper_listing_ids---------------------")
        
        # listing id list of existing data in database
        exclude_scraper_listing_id = list(Products.objects.filter(store_name = data[0]['member_name']).exclude(listing_id__in=scraper_listing_ids).values_list("listing_id", flat=True))
        logging.info(f"{len(exclude_scraper_listing_id)} length of exclude_scraper_listing_id+++++++++++++++++++")
        json_object = json.dumps(data)
 
        # Writing a json file to reduce the request load
        file_path = f"/home/ubuntu/project/app/manual_scrap_json/{data[0]['member_id']}.json"
        with open(file_path, "w") as outfile:
            outfile.write(json_object)

        logging.info(f"{len(data)} length of request data after json dumps")
        # Keeping sleep time while json file if wirting
        time.sleep(30)
        # reading  json file's directory
        dir_files = os.listdir("/home/ubuntu/project/app/manual_scrap_json")
        
        # Loop to creating and updating data by reading response data json file 
        for files in dir_files:
            with open(f'/home/ubuntu/project/app/manual_scrap_json/{files}') as f:
                json_data = json.load(f)
            for row in json_data:
                previous_data = ""
                # Filter data by listing id and current date for update and create data
                is_products = Products.objects.filter(listing_id=row["listing_id"], date=today_date)
                if is_products.exists():
                    previous_data = (
                            is_products.first().quantity_remaining
                            if is_products.first().quantity_remaining
                            else row['quantity_remaining']
                        )
                    previous_sold_product = is_products.first().sold_quantity
                    sold = int(previous_data) - row['quantity_remaining']
                    if sold >= 0:
                        total_sold_quantity = previous_sold_product + sold
                    else:
                        total_sold_quantity = previous_sold_product
                    to_be_update = {"buy_price": row["buy_price"], "available_to_buy": row['quantity_remaining'], "quantity_remaining": row['quantity_remaining'], "sold_quantity" : total_sold_quantity}
                    is_products.update(**to_be_update)
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
            logging.info(
                            f'{current} after endof the function in update------------' 
                        )
            os.remove(f'/home/ubuntu/project/app/manual_scrap_json/{files}')
        payload = json.dumps({"listing_id": exclude_scraper_listing_id})
        headers = {"Content-Type": "application/json"}
        requests.post("http://localhost:5000/listing_id", data=payload, headers=headers)
        logging.info(f"{current} end of scrap_data request function")
        return HttpResponse({"Data store successfully"}, status=200)
    return HttpResponse({"Method Not Allowed"}, status=405)

# @transaction.atomic
# def update_or_create_product(row, today_date):
#     is_products = Products.objects.filter(listing_id=row["listing_id"], date=today_date)
#     if is_products.exists():
#         previous_data = is_products.first().quantity_remaining or row['quantity_remaining']
#         previous_sold_product = is_products.first().sold_quantity
#         sold = int(previous_data) - row['quantity_remaining']
#         total_sold_quantity = previous_sold_product + abs(sold)
#         to_be_update = {"buy_price": row["buy_price"], "available_to_buy": row['quantity_remaining'], "quantity_remaining": row['quantity_remaining'], "sold_quantity" : total_sold_quantity}
#         is_products.update(**to_be_update)
#         logging.info(f"{row['listing_id']} {row['quantity_remaining']} updated successfully")
#     else:
#         Products.objects.create(
#             sku_id=row["sku_id"],
#             store_name=row["member_name"],
#             listing_id=row["listing_id"],
#             date=today_date,
#             title=row["title"],
#             buy_price=row["buy_price"],
#             category_path=row["category_path"],
#             image_url=row['img_url'],
#             photo_id="" if row["photo_id"] == None else row["photo_id"],
#             available_to_buy=row['quantity_remaining'],
#             quantity_remaining=row['quantity_remaining'],
#         )
#         logging.info(f"{row['listing_id']} {row['quantity_remaining']} created successfully")

#     # Products.objects.filter(listing_id=str(row["listing_id"]), sold_quantity=0).delete()

# def wait_and_update(dir_files, today_date):
#     for files in dir_files:
#         with open(f'/home/ubuntu/project/app/listing_id_json/{files}') as f:
#             json_data = json.load(f)
#         for row in json_data:
#             update_or_create_product(row, today_date)
#         logging.info(f"{files} processed")
#         os.remove(f'/home/ubuntu/project/app/listing_id_json/{files}')

# @csrf_exempt
# def listing_cron_scrap_data(request):
#     logging.info("In listing_cron_scrap_data request function")
#     if request.method == "POST":
#         data = json.loads(request.body)
#         products = Products.objects.all()
#         logging.info(f'{len(data)} records received')
#         today_date = str(datetime.now().date().month) + "/" + str(datetime.now().date().year)

#         json_object = json.dumps(data)
#         with open(f"/home/ubuntu/project/app/listing_id_json/{data[0]['member_id']}.json", "w") as outfile:
#             outfile.write(json_object)

#         logging.info("Waiting for previous files to be processed...")
#         while len(os.listdir("/home/ubuntu/project/app/listing_id_json")) > 1:
#             continue

#         dir_files = os.listdir("/home/ubuntu/project/app/listing_id_json")
#         logging.info(f"{len(dir_files)} files found")
#         wait_and_update(dir_files, today_date)

#         logging.info("Function listing_cron_scrap_data completed successfully.")
#         return HttpResponse("OK")

import concurrent.futures

@csrf_exempt
def listing_cron_scrap_data(request):
    logging.info(f"{current} in listing_cron_scrap_data request function")
    if request.method == "POST":
        data = json.loads(request.body)
        today_date = str(datetime.now().date().month) + "/" + str(datetime.now().date().year)
        member_id = data[0]["member_id"]
        
        # Write incoming JSON data to file
        with open(f"/home/ubuntu/project/app/listing_id_json/{member_id}.json", "w") as outfile:
            json.dump(data, outfile)

        # Wait for 10 seconds to ensure file has been written
        time.sleep(10)
        
        # Load all JSON files in directory
        dir_path = "/home/ubuntu/project/app/listing_id_json/"
        logging.info(f"os.listdir(dir_path) listing_cron_scrap_data......................{os.listdir(dir_path)}")
        json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
        json_data = []
        for file in json_files:
            with open(os.path.join(dir_path, file)) as f:
                file_data = json.load(f)
                json_data.extend(file_data)
            os.remove(os.path.join(dir_path, file))  # Remove file after reading its content    s

        # Use a thread pool to update/create products
        args = [(row, today_date) for row in json_data]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(update_or_create_product, args))

        return HttpResponse({"Data stored successfully"}, status=200)

    return HttpResponse({"Method Not Allowed"}, status=405)
@csrf_exempt
def update_or_create_product(args):
    row, today_date = args
    is_product = Products.objects.filter(listing_id=row["listing_id"], date=today_date).first()
    if is_product:
        previous_data = is_product.quantity_remaining or row['quantity_remaining']
        sold = int(previous_data) - int(row['quantity_remaining'])
        if sold >= 0:
            total_sold_quantity = is_product.sold_quantity + sold
        else:
            total_sold_quantity = is_product.sold_quantity
        # total_sold_quantity = is_product.sold_quantity + abs(sold)
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
    # Remove products with sold_quantity = 0
    # Products.objects.filter(listing_id=str(row["listing_id"]), sold_quantity=0).delete()


class TableData(APIView):
    def get(self, request):
        photo_id = request.GET.get("photo_id", "default_value")
        current_month_sold_products_count = (
            Products.objects.filter(photo_id=photo_id)
            .values("photo_id", "date")
            .annotate(total=Sum("sold_quantity"))
            .order_by("-date")
        )
        result_list = []
        for item in current_month_sold_products_count:
            photo_id = item["photo_id"]
            date = item["date"]
            total = item["total"]
            found = False
            for result_dict in result_list:
                if photo_id in result_dict:
                    result_dict[photo_id].append({date: total})
                    found = True
                    break
            if not found:
                result_dict = {photo_id: [{date: total}]}
                result_list.append(result_dict)
        dic = {}
        for d in result_list[0][photo_id]:
            for key, value in d.items():
                dic[key] = value
        labels = dic.keys()
        chartLabel = "Product Data"
        chartdata = dic.values()
        data = {
            "labels": labels,
            "chartLabel": chartLabel,
            "chartdata": chartdata,
        }
        return Response(data)

class AllTableData(APIView):
    def get(self, request):
        photo_id = request.GET.get("photo_id", "default_value")
        photo_id_wise_data = Products.objects.filter(photo_id=photo_id).values(
            "listing_id",
            "title",
            "buy_price",
            "image_url",
            "store_name",
            "sold_quantity",
            "data_updated_at",
        )
        data_list = []
        for filtered_data in photo_id_wise_data:
            data_dict = {}
            utc_time = datetime.fromisoformat(str(filtered_data["data_updated_at"]))
            nz_timezone = pytz.timezone("Pacific/Auckland")
            nz_time = utc_time.astimezone(nz_timezone)
            formatted_time = nz_time.strftime("%Y-%m-%d %I:%M:%S %p")
            data_dict["listing_id"] = filtered_data["listing_id"]
            data_dict["title"] = filtered_data["title"]
            data_dict["buy_price"] = filtered_data["buy_price"]
            data_dict["image_url"] = filtered_data["image_url"]
            data_dict["store_name"] = filtered_data["store_name"]
            data_dict["sold_quantity"] = filtered_data["sold_quantity"]
            data_dict["data_updated_at"] = formatted_time
            data_list.append(data_dict)
        data = {"data_list": data_list}
        return Response(data)


class TestDatatableAPIView(APIView):
    def get(self, request):
        # Get all the data
        request_data = Products.objects.all().values("id","photo_id", "image_url", "title", "store_name","buy_price").distinct()
        current_month_sold_products_count = Products.objects.all().values('photo_id', 'date').annotate(total=Sum('sold_quantity')).order_by("-date")
        
        # Creating a dictionary of all the dates by keeping photo_id as a key 
        result_dict = {}
        for item in current_month_sold_products_count:  
            photo_id = item['photo_id']
            date = item['date']
            total = item['total']
            if photo_id in result_dict:
                result_dict[photo_id].append({date: total})
            else:
                result_dict[photo_id] = [{date: total}]
        
        # Define a function to process data in batches
        def process_data(data):
            response = []
            for i in data:
                updated_queryset_dict = {}
                if i['photo_id'] in result_dict:
                    index = result_dict[i['photo_id']]
                    updated_queryset_dict['id'] = i['id']             
                    updated_queryset_dict['photo_id'] = i['photo_id']
                    updated_queryset_dict['image_url'] = i['image_url']
                    updated_queryset_dict['title'] = i['title']
                    updated_queryset_dict['store_name'] = i['store_name']
                    updated_queryset_dict['buy_price'] = i['buy_price']
                    
                    if len(index) >= 1:
                        updated_queryset_dict['current_month'] = list(index[0].values())[0] if list(index[0].values())[0] else 0
                    else:
                        updated_queryset_dict['current_month'] = 0

                    if len(index) >= 2:
                        updated_queryset_dict['prev_month'] = list(index[1].values())[0] if list(index[1].values())[0] else 0
                    else:
                        updated_queryset_dict['prev_month'] = 0

                    if len(index) >= 3:
                        updated_queryset_dict['sec_prev_month'] = list(index[2].values())[0] if list(index[2].values())[0] else 0
                    else:
                        updated_queryset_dict['sec_prev_month'] = 0

                    response.append(updated_queryset_dict)
            
            return response
        
        # Split the data into batches of 100
        batch_size = 100
        data_batches = [request_data[i:i+batch_size] for i in range(0, len(request_data), batch_size)]
        
        # Define a function to process each batch in a separate thread
        def process_batches():
            threads = []
            responses = []
            for data_batch in data_batches:
                thread = threading.Thread(target=lambda r=data_batch: responses.append(process_data(r)))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            
            # Combine all the responses into one
            final_response = [item for sublist in responses for item in sublist]
            return final_response

        # Call the function to process all batches
        final_response = process_batches()
        
        # Return the final response
        return Response(final_response, status=status.HTTP_200_OK)
    
class TestCsvExport(APIView):
    def post(self, request):
        test_data = Products.objects.filter(store_name = "grabstore")
        export_csv_dir = "/home/ubuntu/project/media/test_csv"
        file_name = "grabstore.csv"
        with open(os.path.join(export_csv_dir, file_name), mode='w', newline='') as export_file:
            writer = csv.writer(export_file)
            writer.writerow(['listing_id', 'title', 'buy_price', 'category_path', 'photo_id', 'image_url',"sku_id", "available_to_buy", "quantity_remaining", 
                             "store_name", "sold_quantity", "date", "data_created_at", "data_updated_at"])
            
            for obj in test_data:
                writer.writerow([obj.listing_id, obj.title, obj.buy_price, obj.category_path, obj.photo_id, obj.image_url, obj.sku_id, obj.available_to_buy, obj.quantity_remaining, 
                                 obj.store_name, obj.sold_quantity, obj.date, obj.data_created_at, obj.data_updated_at])
        return Response("OK")

# def delete_all(request):
#     Store.objects.all().delete()
#     Products.objects.all().delete()
#     SoldProduct.objects.all().delete()
#     return redirect("/")