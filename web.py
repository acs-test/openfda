import http.server
import http.client
import json

OPENFDA_BASIC = True  # Implement the basic or complete requirements

# HTTPRequestHandler class
class OpenFDAHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """ Class that manages the HTTP requests from web clients """

    OPENFDA_API_URL = "api.fda.gov"
    OPENFDA_API_EVENT = "/drug/event.json"

    def get_events(self, limit=10, query=None):
        """ Get the <limit> events from OpenFDA using <query>"""

        conn = http.client.HTTPSConnection(self.OPENFDA_API_URL)
        request = self.OPENFDA_API_EVENT + "?limit=" + str(limit)
        if query is not None:
            request += "&" + query
        conn.request("GET", request)
        events_search = conn.getresponse()
        raw_data = events_search.read()
        events = raw_data.decode("utf8")

        return events


    def get_last_events(self, limit=10):
        """ Get the last <limit> events from OpenFDA """

        return self.get_events(limit)

    def get_events_search_drug(self, drug, limit=10):
        """ Search the last <limit> events from OpenFDA for drug <drug> """
        search_command = 'search=patient.drug.medicinalproduct:' + drug
        return self.get_events(limit, search_command)

    def get_events_search_company(self, company, limit=10):
        """ Search the last <limit> events from OpenFDA for company <company> """
        search_command = 'search=companynumb:' + company
        return self.get_events(limit, search_command)

    def get_list_html(self, items):
        """ Convert a python list to a HTML list """
        html = """
        <html>
			<head>
				<title>OpenFDA Cool App</title>
			</head>
			<body>
                <ol>
        """

        for item in items:
            html += "<li>" + item + "</li>\n"

        html += """
                </ol>
			</body>
        </html>
        """

        return html


    def get_main_page(self):
        """ Return the HTML with the main HTML page """
        if OPENFDA_BASIC:
            with open("openfda_basic.html") as html_file:
                html = html_file.read()
        else:
            with open("openfda.html") as html_file:
                html = html_file.read()

        return html

    def get_not_found_page(self):
        with open("not_found.html") as html_file:
            html = html_file.read()

        return html

    def get_genders_from_events(self, events):
        genders = []
        for event in events:
            genders += [event['patient']['patientsex']]
        return genders

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

        html = ''  # html string to be returned to the client
        limit = 10
        url_found = True

        if self.path == '/':
            html = self.get_main_page()
        elif self.path.startswith('/listGender'):
            if len(self.path.split("=")) > 1 and not OPENFDA_BASIC:
                limit = self.path.split("=")[1]
            events_str = self.get_events(limit)
            events = json.loads(events_str)
            events = events['results']
            genders = self.get_genders_from_events(events)
            html = self.get_list_html(genders)
        elif self.path.startswith('/listDrugs'):
            if len(self.path.split("=")) > 1 and not OPENFDA_BASIC:
                limit = self.path.split("=")[1]
            events_str = self.get_events(limit)
            events = json.loads(events_str)
            events = events['results']
            drugs = self.get_drugs_from_events(events)
            html = self.get_list_html(drugs)
        elif 'searchDrug' in self.path:
            # Get the companies for a drug
            drug = self.path.split("=")[1]
            events_str = self.get_events_search_drug(drug)
            events = json.loads(events_str)
            events = events['results']
            drugs = self.get_companies_from_events(events)
            html = self.get_list_html(drugs)
        elif self.path.startswith('/listCompanies'):
            if len(self.path.split("=")) > 1 and not OPENFDA_BASIC:
                limit = self.path.split("=")[1]
            events_str = self.get_events(limit)
            events = json.loads(events_str)
            events = events['results']
            companies = self.get_companies_from_events(events)
            html = self.get_list_html(companies)
        elif 'searchCompany' in self.path:
            # Get the drugs for a company
            company = self.path.split("=")[1]
            events_str = self.get_events_search_company(company)
            events = json.loads(events_str)
            events = events['results']
            drugs = self.get_drugs_from_events(events)
            html = self.get_list_html(drugs)
        else:
            if not OPENFDA_BASIC:
                url_found = False
                html = self.get_not_found_page()

        # Send response status code
        if not url_found:
            self.send_response(404)
        else:
            self.send_response(200)
        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Write content as utf-8 data
        self.wfile.write(bytes(html, "utf8"))

        return
