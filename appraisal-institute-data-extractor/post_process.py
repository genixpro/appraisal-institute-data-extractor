import time
import csv
import os.path
import re


with open('results.csv', 'rt') as f:
    reader = csv.DictReader(f)
    extracted = list(reader)


cityStateZipRegex = r"(\w+)\s+(\w{2})\s+([0-9]{5})(-[0-9]{4})?"

for item in extracted:
    words = item['data'].split()
    item['searchZip'] = item['zip']
    item['actualZip'] = None
    item['state'] = None
    item['city'] = None
    match = re.search(cityStateZipRegex, item['data'])

    if match:
        item['actualZip'] = match[3]
        item['state'] = match[2]
        item['city'] = match[1]

with open('results.csv', 'wt') as f:
    writer = csv.DictWriter(f, fieldnames=extracted[0].keys())
    writer.writeheader()
    writer.writerows(extracted)
