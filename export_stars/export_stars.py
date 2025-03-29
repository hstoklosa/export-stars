#!env python

import sys
import json
import csv

from math import ceil
from argparse import ArgumentParser

from github import Github
from urllib3 import Retry


def starred_repos(user):
    starred = user.get_starred()
    total_pages = ceil(starred.totalCount / 30)

    for page_num in range(0, total_pages):
        for repo in starred.get_page(page_num):
            yield repo

def config_retry(backoff_factor=1.0, total=8):
    """urllib3 will sleep for:
        {backoff factor} * (2 ** ({number of total retries} - 1))

    Recalculates and Overrides Retry.DEFAULT_BACKOFF_MAX"""
    Retry.DEFAULT_BACKOFF_MAX = backoff_factor * 2 ** (total - 1)
    return Retry(total=total, backoff_factor=backoff_factor)

def parse_args():
    parser = ArgumentParser(description="export a GitHub user's starred repositories")
    parser.add_argument("--user")
    parser.add_argument("--token")
    parser.add_argument("--dest")
    parser.add_argument("--format", choices=["json", "csv"], default="json", 
                       help="Output format (json or csv), defaults to json")
    return parser.parse_args()

def main():
    args = parse_args()
    if not args.user:
        print("Please set `--user` to a valid GitHub user name.", file=sys.stderr)
        exit(1)

    gh = Github(args.token, retry=config_retry()) if args.token else Github(retry=config_retry())
    user = gh.get_user(args.user)
    
    # Collect repositories
    repositories = []
    for repo in starred_repos(user):
        repositories.append({
            "name": repo.name,
            "link": repo.html_url
        })

    # Export based on format
    if args.format == "json":
        if args.dest:
            with open(args.dest, 'w') as f:
                json.dump(repositories, f, indent=2)
        else:
            json.dump(repositories, sys.stdout, indent=2)

    if args.format == "csv":
        if args.dest:
            with open(args.dest, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["name", "link"])
                for repo in repositories:
                    writer.writerow([repo["name"], repo["link"]])
        else:
            writer = csv.writer(sys.stdout)
            writer.writerow(["name", "link"])
            for repo in repositories:
                writer.writerow([repo["name"], repo["link"]])


if __name__ == "__main__":
    main()
