import argparse
import csv
import json
import logging
import re
import sys
from email.parser import HeaderParser
from pathlib import Path

logger = logging.getLogger(__name__)

MESSAGE_DELIMITER = re.compile(
    r"^\s*-{3,}\s*MESSAGE\s*-{3,}\s*$", re.IGNORECASE | re.MULTILINE
)
DOMAIN_PATTERN = re.compile(r"@([\w.-]+)")

SCORE_RETURN_PATH = 35
SCORE_REPLY_TO = 25
SCORE_KEYWORD = 15
SCORE_HOPS = 20
HOPS_THRESHOLD = 4
THRESHOLD_HIGH = 70
THRESHOLD_MEDIUM = 40


def load_suspicious_keywords(keywords_file: Path) -> list[str]:
    """Читає словник стоп-слів (по одному в рядку) у нижньому регістрі."""
    if not keywords_file.exists():
        logger.warning(
            f"Keywords file not found: {keywords_file}. Proceeding without keywords."
        )
        return []
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = [line.strip().lower() for line in f if line.strip()]
    logger.debug(f"Loaded {len(keywords)} suspicious keywords")
    return keywords


def extract_domain(email_str: str) -> str:
    """Повертає домен із адреси (From: Name <user@domain>) у нижньому регістрі."""
    match = DOMAIN_PATTERN.search(email_str)
    return match.group(1).lower().rstrip(".") if match else ""


def _make_record(
    idx: int, from_: str, return_path: str, reply_to: str, subject: str, hops: int
) -> dict:
    return {
        "email_id": f"#{100 + idx}",
        "from": from_.strip(),
        "return_path": return_path.strip(),
        "reply_to": reply_to.strip(),
        "subject": subject.strip(),
        "hops": hops,
    }


def _record_from_text(idx: int, raw_headers: str) -> dict | None:
    """Розбирає один блок текстових заголовків (враховує багаторядкові значення)."""
    msg = HeaderParser().parsestr(raw_headers.strip(), headersonly=True)
    if not (msg.get("From") or msg.get("Subject")):
        return None
    return _make_record(
        idx,
        str(msg.get("From", "")),
        str(msg.get("Return-Path", "")),
        str(msg.get("Reply-To", "")),
        str(msg.get("Subject", "")),
        len(msg.get_all("Received", [])),
    )


def _record_from_mapping(idx: int, item: dict) -> dict | None:
    """Створює запис зі словника JSON (ключі нечутливі до регістру та _/-)."""
    flat = dict(item)
    if isinstance(item.get("headers"), dict):
        flat.update(item["headers"])
    elif isinstance(item.get("headers"), str):
        return _record_from_text(idx, item["headers"])

    norm = {str(k).lower().replace("_", "-"): v for k, v in flat.items()}
    received = norm.get("received", norm.get("hops", []))
    if isinstance(received, list):
        hops = len(received)
    elif isinstance(received, int):
        hops = received
    else:
        text = str(received)
        hops = len(re.findall(r"(?im)^received:", text)) or (1 if text.strip() else 0)

    if not (norm.get("from") or norm.get("subject")):
        return None
    return _make_record(
        idx,
        str(norm.get("from", "")),
        str(norm.get("return-path", "")),
        str(norm.get("reply-to", "")),
        str(norm.get("subject", "")),
        hops,
    )


def _parse_json(content: str) -> list[dict]:
    data = json.loads(content)
    if isinstance(data, dict):
        lists = [v for v in data.values() if isinstance(v, list)]
        data = lists[0] if lists else [data]
    emails = []
    for item in data:
        idx = len(emails) + 1
        if isinstance(item, dict):
            record = _record_from_mapping(idx, item)
        elif isinstance(item, str):
            record = _record_from_text(idx, item)
        else:
            record = None
        if record:
            emails.append(record)
    return emails


def _parse_text(content: str) -> list[dict]:
    if MESSAGE_DELIMITER.search(content):
        blocks = MESSAGE_DELIMITER.split(content)
    else:
        blocks = re.split(r"\n\s*\n", content)
    emails = []
    for block in blocks:
        if not block.strip():
            continue
        record = _record_from_text(len(emails) + 1, block)
        if record:
            emails.append(record)
    return emails


def parse_email_headers(log_file: Path) -> list[dict]:
    """Зчитує дамп заголовків (JSON або текст) і повертає список листів."""
    if not log_file.exists():
        logger.error(f"Mail log file not found: {log_file}")
        return []

    content = log_file.read_text(encoding="utf-8")
    emails: list[dict] = []
    if log_file.suffix.lower() == ".json" or content.lstrip().startswith(("[", "{")):
        try:
            emails = _parse_json(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON ({e}); trying plain-text parser")
            emails = _parse_text(content)
    else:
        emails = _parse_text(content)

    logger.debug(f"Parsed {len(emails)} messages from {log_file}")
    return emails


def analyze_emails(emails: list[dict], keywords: list[str]) -> list[dict]:
    """Обчислює оцінку підозрілості (0-100) та статус кожного листа."""
    results = []

    for email in emails:
        risk_score = 0
        findings = []

        from_domain = extract_domain(email["from"])
        return_domain = extract_domain(email["return_path"])
        reply_domain = extract_domain(email["reply_to"])

        mismatch = False
        if return_domain and from_domain != return_domain:
            mismatch = True
            risk_score += SCORE_RETURN_PATH
            findings.append(
                f"From: '{email['from']}' vs Return-Path: '{email['return_path']}'"
            )

        if reply_domain and from_domain != reply_domain:
            if not mismatch:
                risk_score += SCORE_REPLY_TO
            findings.append(f"Reply-To Mismatch: '{email['reply_to']}'")

        subject_lower = email["subject"].lower()
        found_keywords = [kw.upper() for kw in keywords if kw in subject_lower]
        if found_keywords:
            risk_score += len(found_keywords) * SCORE_KEYWORD
            findings.append(f"Stopwords Found: {found_keywords}")

        if email["hops"] >= HOPS_THRESHOLD:
            risk_score += SCORE_HOPS
            findings.append(
                f"Hop Count: {email['hops']} intermediate relays (Abnormal)"
            )

        risk_score = min(risk_score, 100)

        status = "LOW RISK"
        if risk_score >= THRESHOLD_HIGH:
            status = "HIGH RISK (CRITICAL PHISHING SUSPECT)"
        elif risk_score >= THRESHOLD_MEDIUM:
            status = "MEDIUM RISK"

        logger.debug(f"{email['email_id']}: score={risk_score}, status={status}")
        results.append(
            {
                "email_id": email["email_id"],
                "subject": email["subject"],
                "from": email["from"],
                "return_path": email["return_path"],
                "reply_to": email["reply_to"],
                "hops": email["hops"],
                "risk_score": risk_score,
                "status": status,
                "findings": findings,
            }
        )

    return results


def export_json(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    logger.info(f"Phishing audit summary exported to {output_path}")


def export_csv(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "email_id",
        "subject",
        "from",
        "return_path",
        "reply_to",
        "risk_score",
        "status",
        "hops",
        "findings",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            row_copy = row.copy()
            row_copy["findings"] = " | ".join(row_copy["findings"])
            writer.writerow(row_copy)
    logger.info(f"Phishing audit summary exported to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Email Header & Phishing Indicator Analyzer"
    )
    parser.add_argument(
        "--mail-log", type=Path, required=True, help="Path to email headers dump file"
    )
    parser.add_argument(
        "--suspicious-keywords", type=Path, help="Path to suspicious keywords list"
    )
    parser.add_argument("--out-csv", type=Path, help="Path to CSV report (optional)")
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("labs/lab02/data/phishing_report.json"),
        help="Path to JSON report (default: labs/lab02/data/phishing_report.json)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug-level logging"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(levelname)s] %(message)s",
        force=True,
    )
    logger.info(f"Analyzing email headers dump from {args.mail_log}...")

    keywords = (
        load_suspicious_keywords(args.suspicious_keywords)
        if args.suspicious_keywords
        else []
    )

    try:
        emails = parse_email_headers(args.mail_log)
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f"Cannot read mail log: {e}")
        return 1

    if not emails:
        logger.warning("No email messages parsed.")
        return 1

    logger.info(f"Total emails inspected: {len(emails)}.")
    analyzed = analyze_emails(emails, keywords)

    print("\n=== Phishing & Spoofing Audit Results ===")
    for item in analyzed:
        if item["risk_score"] >= THRESHOLD_MEDIUM:
            print(
                f"[{item['status']}] Email ID {item['email_id']} | "
                f"Risk Score: {item['risk_score']}/100"
            )
            print(f'  Subject: "{item["subject"]}"')
            for finding in item["findings"]:
                print(f"  -> {finding}")
            print("-" * 60)

    try:
        export_json(analyzed, args.out_json)
        if args.out_csv:
            export_csv(analyzed, args.out_csv)
    except OSError as e:
        logger.error(f"Cannot write report: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
