import http.client
import json

headers = {'User-Agent': 'http-client'}


conn = http.client.HTTPSConnection("api.fda.gov")

# Get a  https://api.fda.gov/drug/label.json drug label from this URL and extract what is the id,
# the purpose of the drug and the manufacturer_name

conn.request("GET", "/drug/label.json", None, headers)
r1 = conn.getresponse()
print(r1.status, r1.reason)
drugs_raw = r1.read().decode("utf-8")
conn.close()

drugs = json.loads(drugs_raw)

drug = drugs['results'][0]

drug_id = drug['id']
drug_purpose = drug['purpose'][0]
drug_manufacturer_name = drug['openfda']['manufacturer_name'][0]

print(drug_id, drug_purpose, drug_manufacturer_name)

# Get 10 drugs and extract from all of them the id (tip: use the limit param for it)

conn.request("GET", "/drug/label.json?limit=10", None, headers)
r1 = conn.getresponse()
print(r1.status, r1.reason)
drugs_raw = r1.read().decode("utf-8")
conn.close()

drugs = json.loads(drugs_raw)['results']

for drug in drugs:
    print(drug['id'])

