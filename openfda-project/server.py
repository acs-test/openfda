# Project Final for PNE 2018


import http.server
import json
import socketserver

socketserver.TCPServer.allow_reuse_address = True

PORT = 8000

OPENFDA_BASIC = False

# HTTPRequestHandler class
class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

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

    def build_html_drugs_list(self, drug_items):
        """
        Creates a HTML list string with the drug_items

        :param drug_items: list with the drug items
        :return: string with the HTML list
        """

        html_list = "<ul>"
        for drug in drug_items:
            html_list += "<li>" + drug['id']
            if 'active_ingredient' in drug:
                html_list += " " + drug['active_ingredient'][0]
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                html_list += " " + drug['openfda']['manufacturer_name'][0]
            html_list += "</li>"
        html_list += "</ul>"

        return html_list

    def build_html_companies_list(self, drug_items):
        """
        Creates a HTML list string with the companies in the drug_items

        :param drug_items: list with the drug items
        :return: string with the HTML list
        """

        html_list = "<ul>"
        for drug in drug_items:
            html_list += "<li>"
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                html_list += " " + drug['openfda']['manufacturer_name'][0]
            else:
                html_list += "Unknown"
            html_list += "</li>"
        html_list += "</ul>"

        return html_list

    def build_html_warnings_list(self, drug_items):
        """
        Creates a HTML list string with the warnings in the drug_items

        :param drug_items: list with the drug items
        :return: string with the HTML list
        """

        html_list = "<ul>"
        for drug in drug_items:
            if 'warnings' in drug:
                html_list += "<li>" + drug['warnings'][0]+ "</li>"
            else:
                html_list += "<li>None</li>"
        html_list += "</ul>"

        return html_list


    def get_not_found_page(self):
        with open("not_found.html") as html_file:
            html = html_file.read()

        return html


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
            items = self.search_drugs(active_ingredient, limit)
            http_response = self.build_html_drugs_list(items)
        elif 'listDrugs' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = self.list_drugs(limit)
            http_response = self.build_html_drugs_list(items)
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
            items = self.search_companies(company_name, limit)
            http_response = self.build_html_drugs_list(items)
        elif 'listCompanies' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = self.list_drugs(limit)
            http_response = self.build_html_companies_list(items)
        elif 'listWarnings' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = self.list_drugs(limit)
            http_response = self.build_html_warnings_list(items)
        elif 'secret' in self.path:
            http_response_code = 401
        elif 'redirect' in self.path:
            http_response_code = 302
        else:
            http_response_code = 404
            if not OPENFDA_BASIC:
                url_found = False
                http_response = self.get_not_found_page()

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


Handler = http.server.SimpleHTTPRequestHandler
Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()

# https://github.com/joshmaker/simple-python-webserver/blob/master/server.py
