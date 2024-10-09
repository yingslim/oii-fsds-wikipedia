import argparse
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

DATA_DIR = Path("data")


def download_page_w_revisions(page_title: str, limit: int = 100):
    base_url = "https://en.wikipedia.org/w/index.php"
    params = {
        "title": "Special:Export",
        "pages": page_title,
        "limit": min(limit, 1000),  # Wikipedia API limits to 1000 revisions
        "dir": "desc",
        "action": "submit",
    }
    return requests.post(base_url, data=params).text


def parse_mediawiki_revisions(xml_content):
    soup = BeautifulSoup(xml_content, "lxml-xml")
    for revision in soup.find_all("revision"):
        yield str(revision)


def extract_id(revision: str) -> str:
    return str(_extract_attribute(revision, attribute="id"))


def find_timestamp(revision: str) -> datetime:
    return parse_timestring(_extract_attribute(revision, attribute="timestamp"))


def _extract_attribute(text: str, attribute: str = "timestamp") -> str:
    soup = BeautifulSoup(text, "lxml-xml")
    return soup.find(attribute).text


def parse_timestring(timestring: str) -> datetime:
    return datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%SZ")


def extract_yearmonth(timestamp: datetime) -> str:
    return timestamp.strftime("%Y-%m")


def find_yearmonth(revision: str) -> str:
    return extract_yearmonth(find_timestamp(revision))


def main(page: str, limit: int, data_dir: Path):
    """Downloads the main page (with revisions) for the given page title.
    Organizes the revisions into a folder structure like
    """
    print(f"Downloading {limit} revisions of {page} to {data_dir}")
    raw_revisions = download_page_w_revisions(page, limit=limit)
    print("Downloaded revisions. Parsing and saving...")
    for wiki_revision in tqdm(parse_mediawiki_revisions(raw_revisions), total=limit):
        revision_id = extract_id(wiki_revision)
        year_month = find_yearmonth(wiki_revision)
        revision_path = data_dir / page / year_month / f"{revision_id}.xml"
        if not revision_path.exists():
            revision_path.parent.mkdir(parents=True, exist_ok=True)
        revision_path.write_text(wiki_revision)
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download Wikipedia page revisions",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("page", type=str, help="Title of the Wikipedia page")
    parser.add_argument(
        "--limit", type=int, default=10, help="Number of revisions to download",
    )
    args = parser.parse_args()
    main(page=args.page, limit=args.limit, data_dir=DATA_DIR)
