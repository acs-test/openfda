# Project Final for PNE 2018


import http.server
import json
import socketserver

socketserver.TCPServer.allow_reuse_address = True

PORT = 8000

OPENFDA_BASIC = False


class OpenFDAClient():

    def send_query(self, query):
        """
        Send a query to the OpenFDA API

        :param query: query to be sent
        :return: the result of the query in JSON format
        """

        headers = {'User-Agent': 'http-client'}

        conn = http.client.HTTPSConnection("api.fda.gov")

        # Get a  https://api.fda.gov/drug/label.json drug label from this URL and
        # extract what is the id,
        # the purpose of the drug and the manufacturer_name

        query_url = "/drug/label.json"

        if query:
            query_url += "?" + query

        print("Sending to OpenFDA the query", query_url)

        conn.request("GET", query_url, None, headers)
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        res_raw = r1.read().decode("utf-8")
        conn.close()

        res = json.loads(res_raw)

        return res

    def search_drugs(self, active_ingredient, limit=10):
        """
        Search for drugs given an active ingredient drug_name

        :param drug_name: name of the drug to search
        :param limit: Number of items to be included in the list
        :return: a JSON list with the results
        """

        # drug_name for example: acetylsalicylic

        query = 'search=active_ingredient:"%s"' % active_ingredient

        if limit:
            query += "&limit=" + str(limit)

        drugs = self.send_query(query)

        if 'results' in drugs:
            drugs = drugs['results']
        else:
            drugs = []

        return drugs

    def list_drugs(self, limit=10):
        """
        List default drugs

        :param limit: Number of items to be included in the list
        :return: a JSON list with the results
        """

        query = "limit=" + str(limit)

        drugs = self.send_query(query)

        drugs = drugs['results']

        return drugs

    def search_companies(self, company_name, limit=10):
        """
        Search for companies given a company_name

        :param company_name: name of the company to search
        :return: a JSON list with the results
        """

        query = 'search=openfda.manufacturer_name:"%s"' % company_name

        if limit:
            query += "&limit=" + str(limit)

        drugs = self.send_query(query)

        drugs = drugs['results']

        return drugs


class OpenFDAHTML():

    def build_html_list(self, items):
        """
        Creates a HTML list string with the items

        :param items: list with the items to be included in the HTML list
        :return: string with the HTML list
        """

        html_list = "<ul>"
        for item in items:
            html_list += "<li>" + item + "</li>"
        html_list += "</ul>"

        return html_list


    def get_not_found_page(self):
        with open("not_found.html") as html_file:
            html = html_file.read()

        return html

class OpenFDAParser():

    def parse_companies(self, drugs):
        """
        Given a OpenFDA result, extract the drugs data

        :param drugs: result form a call to OpenFDA drugs API
        :return: list with companies info
        """

        companies = []
        for drug in drugs:
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                companies.append(drug['openfda']['manufacturer_name'][0])
            else:
                companies.append("Unknown")

            companies.append(drug['id'])

        return companies

    def parse_drugs(self, drugs):
        """

        :param drugs: result form a call to OpenFDA drugs API
        :return: list with drugs info
        """

        drugs_labels = []

        for drug in drugs:
            drug_label = drug['id']
            if 'active_ingredient' in drug:
                drug_label += " " + drug['active_ingredient'][0]
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                drug_label += " " + drug['openfda']['manufacturer_name'][0]

            drugs_labels.append(drug_label)

        return drugs_labels

    def parse_warnings(self, drugs):
        """
        Given a OpenFDA result, extract the warnings data

        :param drugs: result form a call to OpenFDA drugs API
        :return: list with warnings info
        """

        warnings = []

        for drug in drugs:
            warnings.append(drug['warnings'][0])

        return warnings


# HTTPRequestHandler class
class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    # GET
    def do_GET(self):
        """
        API to be supported

        searchDrug?drug=<drug_name>
        searchCompany?company=<company_name>
        listDrugs
        listCompanies
        listWarnings
        """

        client = OpenFDAClient()
        html_vis = OpenFDAHTML()
        parser = OpenFDAParser()

        http_response_code = 200
        http_response = "<h1>Not supported</h1>"

        if self.path == "/":
            # Return the HTML form for searching
            with open("openfda.html") as file_form:
                form = file_form.read()
                http_response = form
        elif 'searchDrug' in self.path:
            active_ingredient = None
            limit = 10
            params = self.path.split("?")[1].split("&")
            for param in params:
                param_name = param.split("=")[0]
                param_value = param.split("=")[1]
                if param_name == 'active_ingredient':
                    active_ingredient = param_value
                elif param_name == 'limit':
                    limit = param_value
            items = client.search_drugs(active_ingredient, limit)
            http_response = html_vis.build_html_list(parser.parse_drugs(items))
        elif 'listDrugs' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = client.list_drugs(limit)
            http_response = html_vis.build_html_list(parser.parse_drugs(items))
        elif 'searchCompany' in self.path:
            company_name = None
            limit = 10
            params = self.path.split("?")[1].split("&")
            for param in params:
                param_name = param.split("=")[0]
                param_value = param.split("=")[1]
                if param_name == 'company':
                    company_name = param_value
                elif param_name == 'limit':
                    limit = param_value
            items = client.search_companies(company_name, limit)
            http_response = html_vis.build_html_list(parser.parse_companies(items))
        elif 'listCompanies' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = client.list_drugs(limit)
            http_response = html_vis.build_html_list(parser.parse_companies(items))
        elif 'listWarnings' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = client.list_drugs(limit)
            http_response = html_vis.build_html_list(parser.parse_warnings(items))
        elif 'secret' in self.path:
            http_response_code = 401
        elif 'redirect' in self.path:
            http_response_code = 302
        else:
            http_response_code = 404
            if not OPENFDA_BASIC:
                url_found = False
                http_response = html_vis.get_not_found_page()

        # Send response status code
        self.send_response(http_response_code)

        # Send extra headers headers
        if 'secret' in self.path:
            self.send_header('WWW-Authenticate', 'Basic realm="OpenFDA Private Zone"')
        elif 'redirect' in self.path:
            self.send_header('Location', 'http://localhost:8000/')

        # Send the normal headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Write content as utf-8 data
        self.wfile.write(bytes(http_response, "utf8"))
        return


Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()

# https://github.com/joshmaker/simple-python-webserver/blob/master/server.py
