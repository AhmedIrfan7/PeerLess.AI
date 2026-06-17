"""
Upload fixture PDFs to a running PEERLESS.AI backend and print the browser URLs.

Usage:
    python scripts/demo_upload.py [--base-url http://localhost:8000] [--paper grim_violation]

Papers:  grim_violation  |  pvalue_inconsistency  |  bad_citation  |  clean_paper
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time
import urllib.request

BASE = pathlib.Path(__file__).parent.parent

PAPERS = {
    "grim_violation": BASE / "fixtures" / "grim_violation.pdf",
    "pvalue_inconsistency": BASE / "fixtures" / "pvalue_inconsistency.pdf",
    "bad_citation": BASE / "fixtures" / "bad_citation.pdf",
    "clean_paper": BASE / "fixtures" / "clean_paper.pdf",
}


def upload(base_url: str, pdf_path: pathlib.Path) -> str:
    import json
    import urllib.request
    from urllib.error import URLError

    url = f"{base_url}/api/v1/papers/"
    boundary = "----PeerlessBoundary"
    body_lines = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="file"; filename="{pdf_path.name}"',
        "Content-Type: application/pdf",
        "",
        pdf_path.read_bytes().decode("latin-1"),
        f"--{boundary}--",
    ]
    body = "\r\n".join(body_lines).encode("latin-1")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["paper_id"]
    except URLError as e:
        print(f"ERROR: Cannot reach backend at {base_url}: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description="Upload demo paper and print URLs.")
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--frontend-url", default="http://localhost:3000")
    p.add_argument("--paper", default="grim_violation", choices=list(PAPERS))
    args = p.parse_args()

    pdf = PAPERS[args.paper]
    if not pdf.exists():
        print(f"ERROR: {pdf} not found. Run: python fixtures/make_fixtures.py", file=sys.stderr)
        sys.exit(1)

    print(f"\nUploading {pdf.name} to {args.base_url}...")
    paper_id = upload(args.base_url, pdf)
    paper_url = f"{args.frontend_url}/papers/{paper_id}"

    print(f"\n{'='*55}")
    print(f"  Paper uploaded successfully!")
    print(f"  Paper ID : {paper_id}")
    print(f"{'='*55}")
    print(f"\n  Open in browser:")
    print(f"  {paper_url}")
    print(f"\n  Then click 'Run Integrity Analysis' to start agents.")
    print()


if __name__ == "__main__":
    main()
