import http.server
import json
import socketserver

PORT = 8000

# HTTPRequestHandler class
class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        headers = {'User-Agent': 'http-client'}

        conn = http.client.HTTPSConnection("api.fda.gov")

        # Get a  https://api.fda.gov/drug/label.json drug label from this URL and
        # extract what is the id,
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

        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Send message back to client
        message = drugs[0]['id']
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

Handler = http.server.SimpleHTTPRequestHandler
Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()

# https://github.com/joshmaker/simple-python-webserver/blob/master/server.py
