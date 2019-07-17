import time
import csv
import os.path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions
import traceback
from commonregex import CommonRegex
# from uszipcode import
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import random
from uszipcode import SearchEngine

driver = webdriver.Firefox()
extracted = []
dedupeKeys = set()
existingZipCodes = set()
zipcodeSearch = SearchEngine(simple_zipcode=True)

searchDist = 20
zipCodeSkipDist = 15

def loadExistingResults():
    global existingZipCodes, extracted, dedupeKeys
    if os.path.exists("results.csv"):
        with open('results.csv', 'rt') as f:
            reader = csv.DictReader(f)
            extracted = list(reader)
            dedupeKeys = set(entry['email'] for entry in extracted)
    existingZipCodes = set([entry['zip'] for entry in extracted])


def fetchDataForZipcode(zipCode, initialTimeout=30, refreshTimeout=3):
    driver.get("http://www.myappraisalinstitute.org/findappraiser/")

    elements = driver.find_elements_by_tag_name("input")
    selects = driver.find_elements_by_tag_name("select")

    searchButton = None
    zipField = None
    resultsPerPage = None
    commercialPropertyTypes = None
    distanceField = None
    for elem in (elements + selects):
        id = elem.get_attribute("id")
        if 'ibtn' in id and 'ServiceSearch' in id:
            searchButton = elem
        if 'txt' in id and 'zip' in id:
            zipField = elem
        if 'DDL' in id and 'Within' in id:
            distanceField = elem
        if 'DDL' in id and 'Result' in id:
            resultsPerPage = elem
        if 'DDL' in id and 'CPT' in id:
            commercialPropertyTypes = elem

    for option in distanceField.find_elements_by_tag_name('option'):
        if f'{searchDist} miles' in option.text:
            option.click()
            break

    for option in resultsPerPage.find_elements_by_tag_name('option'):
        if '60' in option.text:
            option.click()
            break

    for option in commercialPropertyTypes.find_elements_by_tag_name('option'):
        if 'Any Commercial' in option.text:
            option.click()
            break

    zipField.clear()
    zipField.send_keys(zipCode)
    searchButton.click()

    WebDriverWait(driver, initialTimeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[src=\"/findappraiser/images/fafwd.jpg\"")))

    time.sleep(1)

    page = 1

    anyNewEntries = extractEntries(zipCode, page)
    writeCurrentResults()
    while hasNextPage() and anyNewEntries:
        nextPage()
        page += 1
        time.sleep(refreshTimeout)
        anyNewEntries = extractEntries(zipCode, page)
        writeCurrentResults()


def extractEntries(zipCode, page):
    entries = driver.find_elements_by_css_selector("td")
    countNewEntries = 0
    countDupes = 0
    countElements = 0
    pageDupes = set()
    for entry in entries:
        children = entry.find_elements_by_css_selector("div b a")

        if len(children) != 1:
            continue

        countElements += 1

        nameElements = entry.find_elements_by_css_selector("div b a")

        name = None
        phone = None
        address = None
        email = None
        url = None

        if nameElements:
            possibleNames = [elem.text for elem in nameElements if elem.text]
            if possibleNames:
                name = possibleNames[0]

        lines = entry.text.splitlines()

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

        dataText = entry.text.replace("\n", " --- ")

        if name or phone or email:
            data = {
                "name": name,
                "phone": phone,
                "address": address,
                "email": email,
                "zip": zipCode,
                "url": url,
                "data": dataText
            }

            dedupeKey = data['email']

            if dedupeKey not in dedupeKeys:
                countNewEntries += 1
                extracted.append(data)
                dedupeKeys.add(dedupeKey)
            elif dedupeKey not in pageDupes:
                countDupes += 1

            pageDupes.add(dedupeKey)

    print(f"    {zipCode}@{page}: Added {countNewEntries} new entries. Had {countDupes} dupes. Examined {countElements} elements")

    return countNewEntries > 0

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


def addNearbyZipsToExistingList(givenZip):
    code = zipcodeSearch.by_zipcode(givenZip)

    # Find nearby zip-codes and add them to the list of zip-codes already handled
    if code.lat and code.lng:
        nearbyZipCodes = list(zipcodeSearch.by_coordinates(code.lat, code.lng, radius=zipCodeSkipDist, returns=1000000))
        skipped = 0
        for nearby in nearbyZipCodes:
            if str(nearby.zipcode) not in existingZipCodes:
                existingZipCodes.add(str(nearby.zipcode))
                skipped += 1
        print(f"    Skipping {skipped} Zip Codes which are within {zipCodeSkipDist} miles of {givenZip}")

def extractAllData():
    allZipCodes = [str(code.zipcode) for code in zipcodeSearch.query(returns=100000000)]
    random.shuffle(allZipCodes)
    for zip in allZipCodes:
        for attempt in range(1, 5):
            try:
                if zip not in existingZipCodes:
                    print(f"Processing {zip}. Handled {len(existingZipCodes)} of {len(allZipCodes)}. {100 * len(existingZipCodes) / len(allZipCodes)}%")
                    fetchDataForZipcode(zip, initialTimeout=30*attempt, refreshTimeout=5*attempt)
                    existingZipCodes.add(zip)
                    addNearbyZipsToExistingList(zip)
                break
            except selenium.common.exceptions.TimeoutException as e:
                print(f"Timeout on {zip}. Retrying.")
                continue
            except Exception as e:
                traceback.print_exc()
                break
        # else:
        #     print("Skipped", str(code.zipcode))

def main():
    print("Loading existing extractions from results.csv")
    loadExistingResults()

    print("Skipping over zip-codes already in DB")
    zipsInDB = list(existingZipCodes)
    for zip in zipsInDB:
        addNearbyZipsToExistingList(zip)

    extractAllData()

    driver.close()



if __name__ == "__main__":
    main()