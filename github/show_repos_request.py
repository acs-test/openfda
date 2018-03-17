import requests

repos_raw = requests.get("https://api.github.com" + "/users/acs-test/repos")

repos = repos_raw.json()

repo = repos[0]
print(repo['owner']['login'])
