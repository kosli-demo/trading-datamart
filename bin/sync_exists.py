#!/usr/bin/env python3                                                                                                                                             
"""Reset the exists field in data/all-repos.json to reflect GitHub reality."""                                                                                     
                                                                                                                                                                    
import json                                                                                                                                                        
import os                                                                                                                                                          
import sys      
import time
import urllib.error
import urllib.request


def repo_exists(github_org, repo_name, token):
    """Return True if github_org/repo_name exists on GitHub, False on 404.
                                                                                                                                                                    
    Retries automatically on 403/429 rate-limit responses, sleeping for the
    duration given in the Retry-After header (defaulting to 60s).                                                                                                  
    """                                                                                                                                                            
    url = f"https://api.github.com/repos/{github_org}/{repo_name}"                                                                                                 
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
                  

def sync_exists(json_path, github_org):
    """Rewrite the exists field for every entry in json_path."""
    token = os.environ.get("GH_TOKEN", "")                                                                                                                         
    with open(json_path) as f:                                                                                                                                     
        repos = json.load(f)                                                                                                                                       
    for repo in repos:                                                                                                                                             
        repo["exists"] = repo_exists(github_org, repo["repo_name"], token)
    with open(json_path, "w") as f:                                                                                                                                
        json.dump(repos, f, indent=2)
        f.write("\n")                                                                                                                                              
                  

if __name__ == "__main__":
    sync_exists("data/all-repos.json", "kosli-demo")
