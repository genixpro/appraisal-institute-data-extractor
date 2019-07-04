import time
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from commonregex import CommonRegex
# from uszipcode import
import json
from uszipcode import SearchEngine

driver = webdriver.Firefox()

extracted = []

with open('results.csv', 'rt') as f:
    reader = csv.DictReader(f)
    extracted = list(reader)

existingZipCodes = set([entry['zip'] for entry in extracted])

raws=[]
dedupeKeys = set()

def fetchDataForZipcode(zipCode):
    driver.get("http://www.myappraisalinstitute.org/findappraiser/")

    elements = driver.find_elements_by_tag_name("input")

    searchButton = None
    zipField = None
    for elem in elements:
        id = elem.get_attribute("id")
        if 'ibtn' in id and 'QCityZipSearch' in id:
            searchButton = elem
        if 'txt' in id and 'ZipQuick' in id:
            zipField = elem



    zipField.clear()
    zipField.send_keys(zipCode)
    searchButton.click()

    time.sleep(6)

    anyNewEntries = extractEntries(zipCode)
    time.sleep(3)
    while hasNextPage() and anyNewEntries:
        nextPage()
        time.sleep(3)
        anyNewEntries = extractEntries(zipCode)
        if anyNewEntries:
            writeCurrentResults()


def extractEntries(zipCode):
    entries = driver.find_elements_by_css_selector("td")
    anyNewEntries = False
    for entry in entries:
        name = entry.find_elements_by_css_selector("a:first-child")
        data = entry.find_elements_by_css_selector("div:nth-child(4)")

        phone = None
        address = None
        email = None
        url = None

        if data:
            lines = data[0].text.splitlines()

            for line in lines:
                parsed_text = CommonRegex(line)

                valid_urls = []
                if hasattr(parsed_text.links, '__call__'):
                    if parsed_text.links():
                        valid_urls = [link for link in parsed_text.links() if 'gmail' not in link and 'yahoo' not in link and 'hotmail' not in 'link']
                else:
                    if parsed_text.links:
                        valid_urls = [link for link in parsed_text.links if 'gmail' not in link and 'yahoo' not in link and 'hotmail' not in 'link']
                if valid_urls:
                    url = valid_urls[0]


                if hasattr(parsed_text.emails, '__call__'):
                    if parsed_text.emails():
                        email = parsed_text.emails()[0]
                else:
                    if parsed_text.emails:
                        email = parsed_text.emails[0]

                if hasattr(parsed_text.phones, '__call__'):
                    if parsed_text.phones():
                        phone = parsed_text.phones()[0]
                else:
                    if parsed_text.phones:
                        phone = parsed_text.phones[0]

                if hasattr(parsed_text.street_addresses, '__call__'):
                    if parsed_text.street_addresses():
                        address = parsed_text.street_addresses()[0]
                else:
                    if parsed_text.street_addresses:
                        address = parsed_text.street_addresses[0]

        # print(name, phone, email)
        if name and phone and email:
            data = {
                "name": [elem.text for elem in name if elem.text][0],
                "phone": phone,
                "address": address,
                "email": email,
                "zip": zipCode,
                "url": url,
                "data": data[0].text.replace("\n", " --- ")
            }

            dedupeKey = data['email']

            if dedupeKey not in dedupeKeys:
                anyNewEntries = True
                extracted.append(data)
                dedupeKeys.add(dedupeKey)
    return anyNewEntries

def hasNextPage():
    nextButton = driver.find_elements_by_css_selector("img[src=\"/findappraiser/images/fafwd.jpg\"")
    if nextButton:
        return True
    else:
        return False

def nextPage():
    nextButton = driver.find_elements_by_css_selector("img[src=\"/findappraiser/images/fafwd.jpg\"")
    if nextButton:
        nextButton[0].click()
        return True
    else:
        return False

def writeCurrentResults():
    with open("results.csv", "wt") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(extracted[0].keys()))
        writer.writeheader()
        writer.writerows(extracted)


search = SearchEngine(simple_zipcode=True)
for code in list(search.query(returns=100000000))[100:]:
    if str(code.zipcode) not in existingZipCodes:
        try:
            fetchDataForZipcode(str(code.zipcode))
        except Exception as e:
            pass
    else:
        print("Skipped", str(code.zipcode))



# elem = driver.find_element_by_name("input")
# elem.clear()
# elem.send_keys(Keys.RETURN)




driver.close()

