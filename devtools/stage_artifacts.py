"""Stage wheels not already listed in a repository's public PyPI simple index.

Uses only the standard library so release jobs need no dependency installation.
The destination must be empty to avoid accidentally uploading stale artifacts.
"""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


class SimpleIndexParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.filenames = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.filenames.add(unquote(urlsplit(href).path.rsplit("/", 1)[-1]))


def existing_filenames(index_url, project):
    request = Request(
        f"{index_url.rstrip('/')}/{project}/", headers={"Accept": "text/html"}
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 404:
            return set()
        raise
    parser = SimpleIndexParser()
    parser.feed(html)
    return parser.filenames


def stage_artifacts(source, destination, index_url):
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError(f"Destination must be empty: {destination}")

    projects = {}
    missing = []
    for wheel in sorted(source.glob("*.whl")):
        project = re.sub(r"[-_.]+", "-", wheel.name.split("-", 1)[0]).lower()
        if project not in projects:
            projects[project] = existing_filenames(index_url, project)
        if wheel.name in projects[project]:
            print(f"Skipping existing artifact: {wheel.name}")
        else:
            missing.append(wheel)

    # Finish all lookups before copying, so lookup errors cannot stage a partial set.
    for wheel in missing:
        print(f"Staging artifact: {wheel.name}")
        shutil.copy2(wheel, destination / wheel.name)
    return len(missing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-url", required=True, help="PyPI simple index URL")
    parser.add_argument("--github-output", type=Path, help="GitHub Actions output file")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    count = stage_artifacts(args.source, args.destination, args.index_url)
    print(f"Staged {count} artifact(s)")
    if args.github_output:
        with args.github_output.open("a") as output:
            output.write(f"count={count}\n")


if __name__ == "__main__":
    main()
