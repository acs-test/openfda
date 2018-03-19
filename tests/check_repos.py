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
import operator
import os
import sys

import requests


GITHUB_REPOS_API = 'https://api.github.com/repos'
GITHUB_USERS_API = 'https://api.github.com/users'
OPENFDA_REPO = "openfda"  # Name of the repository with the practices
PRACTICES_DIRS = ['openfda1', 'openfda2']
REPORT_FILE = 'report.json'


class Report():
    students = 0
    repos_found = 0
    repos_not_found = 0
    repos_not_found_students = []
    repo_ok = 0
    repo_ok_students = []
    repo_ko = 0
    repo_ko_students = []
    repo_main_not_found = 0
    repo_main_not_found_students = []
    students_data = {}

    @staticmethod
    def do_report_json():
        """ Generate the report from a report dict"""

        # List ordered by last modification
        data = Report.students_data

        # login with data as value
        login_date = {}
        for login, value in Report.students_data.items():
            login_date[login] = value['last_commit_date'] if value['last_commit_date'] else ''
        login_date_list = sorted(login_date.items(), key=operator.itemgetter(1), reverse=True)
        print("\nTop Dates\n--------")
        for entry in login_date_list:
            print("{0:25} {1}".format(entry[0], entry[1]))

        # List ordered by number of commits
        top_commits = {login: value['number_commits'] for (login, value) in Report.students_data.items()}
        top_commits_list = sorted(top_commits.items(), key=operator.itemgetter(1), reverse=True)
        print("\nTop Commits\n-----------")
        for entry in top_commits_list:
            print("{0:25} {1}".format(entry[0], entry[1]))

    @staticmethod
    def do_report(report_file=None):
        if not report_file:
            print("Total students", Report.students)
            print("Total repos not found", Report.repos_not_found, Report.repos_not_found_students)
            print("Total %s no found: %i %s" % (OPENFDA_REPO, Report.repo_main_not_found, Report.repo_main_not_found_students))

            print(json.dumps(Report.students_data, indent=True, sort_keys=True))

            freport = open(REPORT_FILE, "w")
            json.dump(Report.students_data, freport, indent=True, sort_keys=True)
            freport.close()
        else:
            print("Generating the report from", REPORT_FILE)
            freport = open(REPORT_FILE)
            Report.students_data = json.load(freport)
            freport.close()

        Report.do_report_json()


def get_params():
    parser = argparse.ArgumentParser(usage="usage:check_repos.py [options]",
                                     description="Check the repos contents from the students in PNE course")
    parser.add_argument("-t", "--token", required=True, help="GitHub API token")
    parser.add_argument("-s", "--students-data", required=True, help="JSON file with students data")

    return parser.parse_args()


def send_github(url, headers=None):
    headers = {'Authorization': 'token ' + args.token}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res


def check_repo(gh_login):
    """ Check is a github user has the openfda repo and it is valid"""

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

        # Check last commit date: get last commit and get the date
        commits_url = GITHUB_REPOS_API + "/" + gh_login + "/" + OPENFDA_REPO + "/commits/master"
        res = send_github(commits_url)
        last_commit_date = res.json()['commit']['committer']['date']

        Report.students_data[gh_login]['last_commit_date'] = last_commit_date
        print("Last commit date", last_commit_date)

        # Check number of commits from the list of contributors
        contribs_url = GITHUB_REPOS_API + "/" + gh_login + "/" + OPENFDA_REPO + "/contributors"
        res = send_github(contribs_url)
        if len(res.json()) > 1:
            print("A student with contributors!", contribs_url)
        commits = 0
        for contributor in res.json():
            commits += int(contributor['contributions'])

        Report.students_data[gh_login]['number_commits'] = commits
        print("Number of commits", commits)

        return check

    repos_url = GITHUB_USERS_API + "/" + gh_login + "/repos"
    page = 1

    check_repos = False  # Check if there are repositories
    check_main_repo = False  # Checks for the main repository
    check_main_repo_not_found = True  # Check if the main repository exists

    while True:
        try:
            res = send_github(repos_url + "?page=%i" % page)
            page += 1  # Prepare for next page request
            res.raise_for_status()
            Report.repos_found += 1
            check_repos = True
        except Exception as ex:
            print(ex)
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
                Report.students_data[gh_login]['url'] = repo['html_url']
                check_main_repo_not_found = False
                check_main_repo = do_checks(repo['url'])
                break

    if check_main_repo_not_found:
        print("Not found %s for %s" % (OPENFDA_REPO, gh_login))
        Report.repo_main_not_found += 1
        Report.repo_main_not_found_students.append(gh_login)

    return check_repos and check_main_repo


if __name__ == '__main__':

    args = get_params()

    if os.path.isfile(REPORT_FILE):
        print("Using the already generated report file", REPORT_FILE)
        Report.do_report(REPORT_FILE)
        sys.exit(0)

    fstudents = open(args.students_data)

    for name, gh_login in json.load(fstudents).items():
        Report.students += 1
        Report.students_data[gh_login] = {
            'last_commit_date': None,
            'number_commits': 0,
            "url": None
        }
        print("Checking repo for", name, gh_login)
        if not check_repo(gh_login):
            print("%s (%s) repo KO" % (name, gh_login))
            Report.repo_ko += 1
            Report.repo_ko_students.append(name)
        else:
            print("%s (%s) repo OK" % (name, gh_login))
            Report.repo_ok += 1
            Report.repo_ok_students.append(name)

    Report.do_report()
