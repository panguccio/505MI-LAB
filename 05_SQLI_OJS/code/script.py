import os
import json

products = json.load(open('/Users/anna/Documents/Uni/CORSI/Magistrale/Anno 2 sem 1/Cybersecurity Lab/505MI-LAB/05_SQLI_OJS/products.json'))
products = products["data"]

ids = []

for product in products:
    ids.append(product["id"])
    if product["deletedAt"] is not None:
        print(product["id"], product["name"])

ids.sort()

all_ids = set(range(1, 56))
deleted = list(all_ids - set(ids))
deleted.sort()

print(f"IDs that don't appear: {deleted}")



