#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Alvaro del Castillo <acs@bitergia.com>

import subprocess
import threading
import time
import unittest

import requests

from html.parser import HTMLParser

class OpenFDAHTMLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.actions_list = []
        self.forms_number = 0
        self.items_number = 0

    def handle_starttag(self, tag, attrs):
        # print("Encountered a start tag:", tag)
        if tag == "form":
            self.forms_number += 1
            for attr in attrs:
                if attr[0] == 'action':
                    self.actions_list.append(attr[1])
        elif tag == "li":
            self.items_number += 1


    def handle_endtag(self, tag):
        # print("Encountered an end tag :", tag)
        pass


    def handle_data(self, data):
        # print("Encountered some data  :", data)
        pass


class WebServer(threading.Thread):
    """ Thread to start the web server """

    def run(self):
        # Start the web server in a thread and kill it after a delay
        cmd = ['python3', 'server.py']
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        TestOpenFDA.WEBSERVER_PROC = proc
        outs, errs = proc.communicate()
        errs_str = errs.decode("utf8")
        if 'Address already in use' in errs_str:
            TestOpenFDA.PORT_BUSY = True
            return

class TestOpenFDA(unittest.TestCase):
    """ Automatic testing for OpenFDA web server main features """
    WEBSERVER_PROC = None
    PORT_BUSY = False
    TEST_PORT = 8000
    TEST_DRUG = 'IBUPROFEN'
    TEST_COMPANY = 'US-PFIZER INC-2014070871'
    TEST_ACTIONS = ['listDrugs', 'searchDrug', 'listCompanies', 'searchCompany', 'listGender']

    @classmethod
    def setUpClass(cls):
        """ Start the web server to be tested """
        WebServer().start()
        # Wait for web sever init code
        time.sleep(1)
        if cls.PORT_BUSY:
            raise RuntimeError("PORT BUSY")

    @classmethod
    def tearDownClass(cls):
        """ Shutdown the webserver """
        cls.WEBSERVER_PROC.kill()

    def test_web_server_init(self):
        resp = requests.get('http://localhost:' + str(self.TEST_PORT))
        # print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        # Remove listGender that it is not in the basic specification
        self.TEST_ACTIONS.remove('listGender')
        try:
            parser.actions_list.remove('listGender')
        except ValueError:
            # The form does not include this option
            pass
        self.assertEqual(len(parser.actions_list), 4)
        self.assertEqual(set(self.TEST_ACTIONS), set(parser.actions_list))
        self.TEST_ACTIONS.append('listGender')

    def test_web_server_init_gender(self):
        # In the complete project a listGender is included
        resp = requests.get('http://localhost:' + str(self.TEST_PORT))
        # print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.forms_number, 5)
        self.assertEqual(set(self.TEST_ACTIONS), set(parser.actions_list))

    def test_list_drugs(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listDrugs?limit=10'
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_list_drugs_limit(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listDrugs?limit=22'
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 22)

    def test_search_drug(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/searchDrug?drug=' + self.TEST_DRUG
        resp = requests.get(url)
        # print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_list_companies(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listCompanies?limit=10'
        resp = requests.get(url)
        # print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_list_gender(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listGender?limit=10'
        resp = requests.get(url)
        # print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_search_company(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/searchCompany?company=' + self.TEST_COMPANY
        resp = requests.get(url)
        # print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_not_found(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/not_exists_resource'
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_redirect(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/redirect'
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)

if __name__ == "__main__":
    unittest.main(warnings='ignore')
