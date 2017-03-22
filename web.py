import http.server
import http.client
import json


OPENFDA_API_EVENT = "/drug/event.json"


# HTTPRequestHandler class
class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    OPENFDA_API_URL = "api.fda.gov"
    OPENFDA_API_EVENT = "/drug/event.json"

    def get_events(self):
        ###
        # GET EVENTS
        ##

        conn = http.client.HTTPSConnection(self.OPENFDA_API_URL)
        conn.request("GET", self.OPENFDA_API_EVENT + "?limit=10")
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        # 200 OK
        data1 = r1.read()
        data1 = data1.decode("utf8")
        events = data1

        return events

    def get_events_search(self, drug_search):
        ###
        # GET EVENTS
        ##

        conn = http.client.HTTPSConnection(self.OPENFDA_API_URL)
        search_command = 'search=patient.drug.medicinalproduct:' + drug_search
        conn.request("GET", self.OPENFDA_API_EVENT + "?limit=10&"+search_command)
        r1 = conn.getresponse()
        data1 = r1.read()
        data1 = data1.decode("utf8")
        event = data1

        return event

    def get_list_html(self, drugs):
        drugs_html = """
        <html>
			<head>
				<title>OpenFDA Cool App</title>
			</head>
			<body>
                <ul>
        """

        for drug in drugs:
            drugs_html += "<li>" + drug + "</li>\n"

        drugs_html += """
                </ul>
			</body>
        </html>
        """

        return drugs_html


    def get_main_page(self):
        html = """
        <html>
			<head>
				<title>OpenFDA Cool App</title>
			</head>
			<body>
				<h1>OpenFDA Client</h1>
				<form method="get" action="receive">
                    <input type="button">
					<input type="submit" value="Drug List: Send to OpenFDA"></input>
				</form>
				<form method="get" action="search">
                    <input type="text" name="drug"></input>
					<input type="submit" value="Drug Search LYRICA: Send to OpenFDA"></input>
				</form>
			</body>
        </html>
        """

        return html

    def get_drugs_from_events(self, events):
        drugs = []
        for event in events:
            drugs += [event['patient']['drug'][0]['medicinalproduct']]
        return drugs

    def get_companies_from_events(self, events):
        companies = []
        for event in events:
            companies += [event['companynumb']]
        return companies

    # GET
    def do_GET(self):

        main_page = False
        is_event = False
        is_search = False
        if self.path == '/':
            main_page = True
        elif self.path == '/receive?':
            is_event = True
        elif 'search' in self.path:
            is_search = True


        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Write content as utf-8 data
        html = ''  # html string to be returned to the client

        if main_page:
            html = self.get_main_page()
        elif is_event:
            events_str = self.get_events()
            events = json.loads(events_str)
            events = events['results']
            drugs = self.get_drugs_from_events(events)
            html = self.get_list_html(drugs)
        elif is_search:
            # /search?drug=IBUPROFENO
            drug = self.path.split("=")[1]
            events_str = self.get_events_search(drug)
            events = json.loads(events_str)
            events = events['results']
            drugs = self.get_companies_from_events(events)
            html = self.get_list_html(drugs)

        self.wfile.write(bytes(html, "utf8"))

        return
