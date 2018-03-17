import http.client
import json

headers = {'User-Agent': 'http-client'}


# Using https://api.fda.gov/drug/label.json send a query to find the products related to aspirins
# https://api.fda.gov/drug/label.json?search=active_ingredient:"acetylsalicylic"&limit=100

conn = http.client.HTTPSConnection("api.fda.gov")


query = 'search=active_ingredient:"acetylsalicylic"'
limit = 10  # Get all the results. In this case it is 4.

url_path = "/drug/label.json" + "?" + query + "&" + "limit=" + str(limit)

conn.request("GET", url_path, None, headers)



r1 = conn.getresponse()
print(r1.status, r1.reason)
drugs_raw = r1.read().decode("utf-8")
conn.close()

aspirins = json.loads(drugs_raw)
aspirins_list = aspirins['results']

# Print the name of all manufacturers which produce aspirins

for aspirin in aspirins_list:
    if aspirin['openfda']:
        print(aspirin['openfda']['manufacturer_name'][0])
    else:
        print("Manufacturer not found")