#!/usr/bin/env python3
"""Find repos in all-repos.json that exist but are missing source/datetime.txt."""

import json
import os
import sys
import time
import urllib.error
import urllib.request


def file_exists_in_repo(github_org, repo_name, file_path, token):
    """Return True if file_path exists in github_org/repo_name, False on 404.

    Retries automatically on 403/429 rate-limit responses, sleeping for the
    duration given in the Retry-After header (defaulting to 60s).
    """
    url = f"https://api.github.com/repos/{github_org}/{repo_name}/contents/{file_path}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    while True:
        try:
            urllib.request.urlopen(req)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            if e.code in (403, 429):
                retry_after = int(e.headers.get("Retry-After", 60))
                print(f"Rate limited; retrying after {retry_after}s", file=sys.stderr)
                time.sleep(retry_after)
            else:
                raise


def find_missing(json_path, github_org):
    """Return list of repo name dicts where exists=true but source/datetime.txt is absent."""
    token = os.environ.get("GH_TOKEN", "")
    with open(json_path) as f:
        repos = json.load(f)
    missing = []
    for repo in repos:
        if not repo.get("exists"):
            continue
        repo_name = repo["repo_name"]
        if not file_exists_in_repo(github_org, repo_name, "source/datetime.txt", token):
            print(f"MISSING: {repo_name}", file=sys.stderr)
            missing.append({"repo_name": repo_name})
        else:
            print(f"ok: {repo_name}", file=sys.stderr)
    return missing


if __name__ == "__main__":
    missing = find_missing("data/all-repos.json", "kosli-demo")
    print(json.dumps(missing))
