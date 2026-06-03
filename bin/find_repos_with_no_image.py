#!/usr/bin/env python3
"""
Find repos in all-repos.json that do not have a ghcr.io docker image
For example, in all-repos.json there is
  {
    "repo_name": "trade-statement",
    "exists": true,
    "has_junit": true
  },
so we need to check if ghcr.io/kosli-demo/trade-statement:latest exists or not.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _get_registry_token(owner, repo, gh_token):
    """Fetch a pull-scoped Bearer token for the ghcr.io registry."""
    url = f"https://ghcr.io/token?scope=repository:{owner}/{repo}:pull&service=ghcr.io"
    req = urllib.request.Request(url)
    if gh_token:
        credentials = base64.b64encode(f"token:{gh_token}".encode()).decode()
        req.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["token"]


def image_exists(owner, repo, tag="latest"):
    """Return True if the ghcr.io image manifest exists, False on 404.

    Retries automatically on 403/429 rate-limit responses, sleeping for the
    duration given in the Retry-After header (defaulting to 60s).
    """
    gh_token = os.environ.get("GH_TOKEN", "")
    bearer = _get_registry_token(owner, repo, gh_token)

    url = f"https://ghcr.io/v2/{owner}/{repo}/manifests/{tag}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {bearer}")
    req.add_header("Accept", "application/vnd.oci.image.manifest.v1+json")
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


def find_repos(json_path, github_org, limit=200):
    """Return up to `limit` repos that have no ghcr.io image.

    GitHub Actions caps matrix configurations at 256; limit keeps us safely
    under that ceiling. Re-running the workflow picks up the next batch since
    this script only returns repos that are still missing an image.
    """
    with open(json_path) as f:
        repos = json.load(f)
    results = []
    for repo in repos:
        if len(results) >= limit:
            break
        repo_name = repo["repo_name"]
        if not image_exists(github_org, repo_name):
            results.append({"repo_name": repo_name})
    return results


if __name__ == "__main__":
    results = find_repos("data/all-repos.json", "kosli-demo")
    print(json.dumps(results))
