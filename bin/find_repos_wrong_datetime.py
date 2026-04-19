#!/usr/bin/env python3
"""Find repos in all-repos.json that exist but are missing source/datetime.txt
or have content that does not match '<repo_name> <unix_epoch_timestamp>'."""

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request


def get_file_content(github_org, repo_name, file_path, token):
    """Return decoded text content of file_path in github_org/repo_name, or None on 404.

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
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                return base64.b64decode(data["content"]).decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (403, 429):
                retry_after = int(e.headers.get("Retry-After", 60))
                print(f"Rate limited; retrying after {retry_after}s", file=sys.stderr)
                time.sleep(retry_after)
            else:
                raise


def content_is_valid(repo_name, content):
    """Return True if content matches '<repo_name> <unix_epoch_integer>'."""
    return bool(re.match(rf"^{re.escape(repo_name)} \d+$", content.strip()))


def find_wrong(json_path, github_org):
    """Return list of repo name dicts where exists=true but source/datetime.txt is absent or invalid."""
    token = os.environ.get("GH_TOKEN", "")
    with open(json_path) as f:
        repos = json.load(f)
    results = []
    for repo in repos:
        if not repo["exists"]:
            continue
        repo_name = repo["repo_name"]
        content = get_file_content(github_org, repo_name, "source/datetime.txt", token)
        if content is None:
            print(f"MISSING: {repo_name}", file=sys.stderr)
            results.append({"repo_name": repo_name})
        elif not content_is_valid(repo_name, content):
            print(f"INVALID: {repo_name} (content={content!r})", file=sys.stderr)
            results.append({"repo_name": repo_name})
        else:
            print(f"ok: {repo_name}", file=sys.stderr)
    return results


if __name__ == "__main__":
    results = find_wrong("data/all-repos.json", "kosli-demo")
    print(json.dumps(results))
