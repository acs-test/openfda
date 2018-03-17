#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Get the GitHub repos from PNE course students
#
# Copyright (C) Alvaro del Castillo
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

import argparse
import json

import requests

GITHUB_REPOS_API = 'https://api.github.com/repos'
GITHUB_USERS_API = 'https://api.github.com/users'
OPENFDA_REPO = "openfda"  # Name of the repository with the practices
PRACTICES_DIRS = ['openfda1', 'openfda2']

class Report():
    students = 0
    repos_found = 0
    repos_not_found = 0
    repos_not_found_students = []
    repos_ok = 0
    repos_ok_students = []
    repos_ko = 0
    repos_ko_students = []

    @staticmethod
    def do_report():
        print ("Total students", Report.students)
        print("Total repos not found", Report.repos_not_found, Report.repos_not_found_students)


def get_params():
    parser = argparse.ArgumentParser(usage="usage:check_repos.py [options]",
                                     description="Check the repos contents from the students in PNE course")
    parser.add_argument("-t", "--token", required=True, help="GitHub API token")
    parser.add_argument("-s", "--students-data", required=True, help="JSON file with students data")

    return parser.parse_args()

def send_github(url, headers=None):
    headers = {'Authorization': 'token ' + args.token }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res

def check_repo(gh_login):
    """ Check is a github user has the openfda repo and it is valid"""
    repos_url = GITHUB_USERS_API + "/" + gh_login + "/repos"
    page = 1

    def do_checks(gh_repo):
        """

        :rtype: Boolean with the result of the checks
        """

        check = False

        print("Checking", gh_repo)
        # Checks that practices exists
        practices_pending = list(PRACTICES_DIRS)
        res = send_github(gh_repo + "/contents")
        res.raise_for_status()

        for content in res.json():
            if content['type'] == "dir":
                try:
                    practices_pending.remove(content['name'])
                except ValueError:
                    pass

        if not practices_pending:
            print("All practices found")
            check = True
        else:
            print("Practices not found for %s: %s" % (gh_repo, practices_pending))
            check = False

        # Check number of commits
        # Check last commit date

        return check


    check = False

    while True:
        try:
            res = send_github(repos_url + "?page=%i" % page)
            page += 1  # Prepare for next page request
            res.raise_for_status()
            Report.repos_found += 1
        except Exception:
            print("Can not find", repos_url)
            Report.repos_not_found += 1
            Report.repos_not_found_students.append(gh_login)
            break

        repos_dict = res.json()

        if not repos_dict:
            break

        for repo in repos_dict:
            if repo['name'] != OPENFDA_REPO:
                continue
            else:
                print("Found repo %s for %s" % (repo['name'], gh_login))
                check = do_checks(repo['url'])

    return check


if __name__ == '__main__':

    args = get_params()

    fstudents = open(args.students_data)


    for name, gh_login in json.load(fstudents).items():
        Report.students += 1
        print("Checking repo for", name, gh_login)
        if not check_repo(gh_login):
            print("%s (%s) repo KO" % (name, gh_login))
            Report.repos_ko += 1
            Report.repos_ko_students.append(name)
        else:
            print("%s (%s) repo OK" % (name, gh_login))
            Report.repos_ok += 1
            Report.repos_ok_students.append(name)

    Report.do_report()

