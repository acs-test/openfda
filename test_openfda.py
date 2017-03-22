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
    def handle_starttag(self, tag, attrs):
        print("Encountered a start tag:", tag)

    def handle_endtag(self, tag):
        print("Encountered an end tag :", tag)

    def handle_data(self, data):
        print("Encountered some data  :", data)


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
        print(resp.text)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)


    def test_list_drugs(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listDrugs'
        resp = requests.get(url)
        print(resp.text)

    def test_search_drug(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/searchDrug?drug=' + self.TEST_DRUG
        resp = requests.get(url)
        print(resp.text)

    def test_list_companies(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listCompanies'
        resp = requests.get(url)
        print(resp.text)

    def test_search_company(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/searchCompany?company=' + self.TEST_COMPANY
        resp = requests.get(url)
        print(resp.text)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
