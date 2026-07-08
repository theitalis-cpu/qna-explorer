import json
import re
from html import unescape
from pathlib import Path


def normalize_qna(item):
    qid = item.get("qid") or item.get("id")
    if qid is None:
        raise ValueError("Q&A item is missing qid")
    date = str(item.get("questionDate") or item.get("date") or "")[:10]
    return {
        "qid": int(qid),
        "question": item.get("question") or "",
        "answer": item.get("answer") or "",
        "questionDate": date,
        "qacat": item.get("qacat") or item.get("cat") or "",
    }


def load_qna_file(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = raw.values() if isinstance(raw, dict) else raw
    rows = [normalize_qna(item) for item in items]
    rows.sort(key=lambda row: row["qid"], reverse=True)
    return rows


def write_qna_file(path, rows):
    normalized = [normalize_qna(row) for row in rows]
    normalized.sort(key=lambda row: row["qid"], reverse=True)
    Path(path).write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def filter_qas(rows, query="", category=""):
    query = (query or "").strip().lower()
    category = category or ""
    out = []
    for row in rows:
        if category and row.get("qacat") != category:
            continue
        if query:
            haystack = f"{row.get('qid', '')} {row.get('question', '')} {row.get('answer', '')}".lower()
            if query not in haystack:
                continue
        out.append(row)
    return out


def _clean_html_text(fragment):
    fragment = re.sub(r"<span[^>]*>\s*(?:שאלה|תשובה):\s*</span>", "", fragment)
    fragment = re.sub(r"<br[^>]*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return unescape(fragment).strip()


def parse_qas_listing(html):
    cards = re.findall(
        r'<div[^>]+class="[^"]*answer-content[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html,
        flags=re.S,
    )
    if not cards:
        cards = re.findall(
            r'<div[^>]+class="[^"]*answer-content[^"]*"[^>]*>(.*?)(?=<div[^>]+class="[^"]*answer-content|\Z)',
            html,
            flags=re.S,
        )

    rows = []
    for card in cards:
        qid_match = re.search(r'href="/qas/(\d+)"', card) or re.search(r'answer-id-home[^>]*>\s*(\d+)\s*<', card)
        q_match = re.search(r"<span[^>]*>\s*שאלה:\s*</span>(.*?)(?=<span[^>]*>\s*תשובה:|</p>)", card, flags=re.S)
        a_match = re.search(r"<span[^>]*>\s*תשובה:\s*</span>(.*?)(?:</p>|</div>)", card, flags=re.S)
        if not (qid_match and q_match and a_match):
            continue
        rows.append({
            "qid": int(qid_match.group(1)),
            "question": _clean_html_text(q_match.group(1)),
            "answer": _clean_html_text(a_match.group(1)),
            "questionDate": "",
            "qacat": "",
        })
    return rows


def merge_qas(existing, incoming):
    merged = {normalize_qna(row)["qid"]: normalize_qna(row) for row in existing}
    for row in incoming:
        normalized = normalize_qna(row)
        if normalized["question"] or normalized["answer"]:
            merged[normalized["qid"]] = normalized
    rows = list(merged.values())
    rows.sort(key=lambda row: row["qid"], reverse=True)
    return rows
