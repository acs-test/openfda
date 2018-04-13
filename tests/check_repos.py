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
import subprocess

import requests


GITHUB_URL = 'https://github.com'
GITHUB_REPOS_API = 'https://api.github.com/repos'
GITHUB_USERS_API = 'https://api.github.com/users'
OPENFDA_REPO = "openfda"  # Name of the repository with the practices
PRACTICES_DIRS = ['openfda-1', 'openfda-2', 'openfda-3', 'openfda-4']
PROJECT_DIR = 'openfda-project'
STUDENT_RESULTS_FILE = 'report.json'

class Evaluator():
    """ Evaluator get all practices from GitHub and evaluate them """

    @staticmethod
    def execute_cmd(cmd, cwd):
        """ Execute a shell command analyzing the output and errors """
        print("Executing the command", cmd, os.getcwd())
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        outs, errs = proc.communicate()
        outs_str = outs.decode("utf8")
        errs_str = errs.decode("utf8")

        return errs_str, outs_str

    @staticmethod
    def evalute_students(students_data):
        """
        Evaluate the practices for the github logins included in students_data
        :param students_data: github logins to evaluate
        :return:
        """

        for name, gh_login in students_data.items():
            # Check that the repository exists
            check_url = "https://api.github.com/repos/%s/%s" % (gh_login, OPENFDA_REPO)
            res = requests.get(check_url)

            if res.status_code == 200:
                print("Cloning for %s the repository %s" % (gh_login, OPENFDA_REPO))
                clone_url = GITHUB_URL + "/" + gh_login + "/" + OPENFDA_REPO
                cmd = ['git', 'clone', clone_url, 'repos/openfda-' + gh_login]

                print (Evaluator.execute_cmd(cmd, "."))
            else:
                print("Repository not found for", gh_login)



class Report():
    """ This Report is useful to track the activity of students in GitHub """
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
    students_res = {}

    @staticmethod
    def check_repo(gh_login):
        """
        Check is a github user has the openfda repo and its contents

        :param gh_login: github login for the user to test
        :return:
        """

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

            # Add the practices pending data
            Report.students_res[gh_login]['practices_pending'] = practices_pending
            Report.students_res[gh_login]['number_practices_found'] = len(PRACTICES_DIRS) - len(practices_pending)

            # Check last commit date: get last commit and get the date
            commits_url = GITHUB_REPOS_API + "/" + gh_login + "/" + OPENFDA_REPO + "/commits/master"
            res = send_github(commits_url)
            last_commit_date = res.json()['commit']['committer']['date']

            Report.students_res[gh_login]['last_commit_date'] = last_commit_date
            print("Last commit date", last_commit_date)

            # Check number of commits from the list of contributors
            contribs_url = GITHUB_REPOS_API + "/" + gh_login + "/" + OPENFDA_REPO + "/contributors"
            res = send_github(contribs_url)
            if len(res.json()) > 1:
                print("A student with contributors!", contribs_url)
            commits = 0
            for contributor in res.json():
                commits += int(contributor['contributions'])

            Report.students_res[gh_login]['number_commits'] = commits
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
                    Report.students_res[gh_login]['url'] = repo['html_url']
                    check_main_repo_not_found = False
                    check_main_repo = do_checks(repo['url'])
                    break

        if check_main_repo_not_found:
            print("Not found %s for %s" % (OPENFDA_REPO, gh_login))
            Report.repo_main_not_found += 1
            Report.repo_main_not_found_students.append(gh_login)

        return check_repos and check_main_repo

    @staticmethod
    def fetch_report_data(students_data):
        """
        Fetch the data from GitHub to generate the report

        :param students_data: dict with the logins in github of the students
        :return: None, it fills the report data
        """

        for name, gh_login in students_data.items():
            Report.students += 1
            Report.students_res[gh_login] = {
                'last_commit_date': None,
                'number_commits': 0,
                'number_practices_found': 0,
                'practices_pending': [],
                'project_found': False,
                "url": None
            }
            print("Checking repo for", name, gh_login)
            try:
                if not Report.check_repo(gh_login):
                    print("%s (%s) repo KO" % (name, gh_login))
                    Report.repo_ko += 1
                    Report.repo_ko_students.append(name)
                else:
                    print("%s (%s) repo OK" % (name, gh_login))
                    Report.repo_ok += 1
                    Report.repo_ok_students.append(name)
            except Exception as ex:
                print("Can't not get data from %s (%s)" % (name, gh_login))
                print(ex)

    @staticmethod
    def show():
        """ Generate the report from a report dict"""

        # List ordered by last modification
        login_date = {}
        for login, value in Report.students_res.items():
            login_date[login] = value['last_commit_date'] if value['last_commit_date'] else ''
        login_date_list = sorted(login_date.items(), key=operator.itemgetter(1), reverse=True)
        print("\nTop Dates\n--------")
        for entry in login_date_list:
            print("{0:25} {1}".format(entry[0], entry[1]))

        # List ordered by number of commits
        top_commits = {login: value['number_commits'] for (login, value) in Report.students_res.items()}
        top_commits_list = sorted(top_commits.items(), key=operator.itemgetter(1), reverse=True)
        print("\nTop Commits\n-----------")
        for entry in top_commits_list:
            print("{0:25} {1}".format(entry[0], entry[1]))

        # List ordered by number of practices
        top_practices = {login: value['number_practices_found'] for (login, value) in Report.students_res.items()}
        top_practices_list = sorted(top_practices.items(), key=operator.itemgetter(1), reverse=True)
        print("\nTop Practices\n-----------")
        for entry in top_practices_list:
            print("{0:25} {1}".format(entry[0], entry[1]))


    @staticmethod
    def do_report(students_data=None, students_res=None):
        """
        Generate the report for the activity of the students in GitHub

        :param students_data: dict with the logins of the students
        :param students_res: an already generated report with students results
        :return:
        """
        if not students_res:
            # If the data is not collected yet, collect it
            Report.fetch_report_data(students_data)

            print("Total students", Report.students)
            print("Total repos not found", Report.repos_not_found, Report.repos_not_found_students)
            print("Total %s no found: %i %s" % (OPENFDA_REPO, Report.repo_main_not_found, Report.repo_main_not_found_students))

            print(json.dumps(Report.students_res, indent=True, sort_keys=True))

            freport = open(STUDENT_RESULTS_FILE, "w")
            json.dump(Report.students_res, freport, indent=True, sort_keys=True)
            freport.close()
        else:
            Report.students_res = students_res

        Report.show()


def get_params():
    parser = argparse.ArgumentParser(usage="usage:check_repos.py [options]",
                                     description="Check the repos contents from the students in PNE course")
    parser.add_argument("-t", "--token", required=True, help="GitHub API token")
    parser.add_argument("-s", "--students-data", required=True, help="JSON file with students data")
    parser.add_argument("-r", "--report", action='store_true', default=True, help="Generate the activity report")
    parser.add_argument("-e", "--evaluate", action='store_true', help="Generate the scores report")

    return parser.parse_args()


def send_github(url, headers=None):
    headers = {'Authorization': 'token ' + args.token}
    res = requests.get(url, headers=headers)
    try:
        res.raise_for_status()
    except requests.exceptions.HTTPError:
        print("Can not get repository data (is empty?) from", url)
    return res


if __name__ == '__main__':

    args = get_params()

    if args.report and not args.evaluate:
        print("Generating the activity report")
        if os.path.isfile(STUDENT_RESULTS_FILE):
            print("Using the already generated students results", STUDENT_RESULTS_FILE)
            with open(STUDENT_RESULTS_FILE) as file_results_data:
                Report.do_report(students_res=json.load(file_results_data))
        else:
            with open(args.students_data) as file_student_data:
                Report.do_report(students_data=json.load(file_student_data))
    else:
        print("Evaluating the practices")
        with open(args.students_data) as file_student_data:
            Evaluator.evalute_students(json.load(file_student_data))
