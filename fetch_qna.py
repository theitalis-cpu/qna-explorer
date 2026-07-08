from pathlib import Path
from urllib.request import Request, urlopen

from qna_pipeline import load_qna_file, merge_qas, parse_qas_listing, write_qna_file


BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "qna_data.json"
SOURCE_URL = "https://dtz.sbms.io/qas"
USER_AGENT = "Mozilla/5.0 (compatible; qna-explorer-updater/1.0)"


def fetch_text(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def main():
    existing = load_qna_file(DATA_PATH) if DATA_PATH.exists() else []
    html = fetch_text(SOURCE_URL)
    incoming = parse_qas_listing(html)
    merged = merge_qas(existing, incoming)
    write_qna_file(DATA_PATH, merged)
    print(f"Fetched {len(incoming)} live questions; qna_data.json now has {len(merged)} questions.")


if __name__ == "__main__":
    main()
