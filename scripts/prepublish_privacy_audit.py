#!/usr/bin/env python3
"""Conservative, dependency-free privacy check for this personal website.

Run this after building the site and before every public push.  It does not
replace a human review of new PDFs or photographs; it catches common accidental
disclosures and forces every public PDF to be explicitly approved below.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# These addresses are intentionally public or belong to retained AcademicPages
# template source. Any new address must be reviewed before it is added here.
APPROVED_EMAILS = {
    "jzhang3450@gatech.edu",
    "mushishi78@gmail.com",
    "name@name.com",
    "name2@name2.com",
    "none@example.org",
}

# A PDF is public only after a manual page-by-page privacy review.
APPROVED_PUBLIC_PDFS = {
    "files/research/jingyi-zhang-masters-thesis-2021.pdf",
    "files/teaching/thank-a-teacher-fall-2025-note-1.pdf",
    "files/teaching/thank-a-teacher-fall-2025-note-2.pdf",
}

TEMPLATE_PDFS = {
    "files/paper1.pdf",
    "files/paper2.pdf",
    "files/paper3.pdf",
    "files/slides1.pdf",
    "files/slides2.pdf",
    "files/slides3.pdf",
}

SKIP_DIRS = {
    ".bundle",
    ".git",
    ".jekyll-cache",
    ".sass-cache",
    "_site",
    "node_modules",
    "tmp",
    "vendor",
}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rb",
    ".scss",
    ".sh",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

PUBLIC_IMAGE_ROOTS = (
    ROOT / "images" / "awards",
    ROOT / "images" / "projects",
    ROOT / "images" / "teaching",
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
# macOS user paths can reveal a local account name. Generic container paths
# such as /home/vscode/ are intentionally not treated as personal data.
LOCAL_PATH_RE = re.compile(r"/Users/[^/\s]+/")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
}
SENSITIVE_FILENAMES = re.compile(
    r"(?:^|/)(?:\.env(?:\..+)?|credentials(?:\..+)?|id_rsa|id_ed25519)$|\.(?:key|p12|pfx|pem)$",
    re.IGNORECASE,
)


def repo_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return files


def inspect_text(path: Path, errors: list[str]) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES or path.name.endswith(".min.js"):
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return

    relative = path.relative_to(ROOT).as_posix()
    for email in sorted(set(EMAIL_RE.findall(text)) - APPROVED_EMAILS):
        errors.append(f"unapproved email in {relative}: {email}")
    for phone in sorted(set(PHONE_RE.findall(text))):
        errors.append(f"possible phone number in {relative}: {phone}")
    if relative != "scripts/prepublish_privacy_audit.py" and LOCAL_PATH_RE.search(text):
        errors.append(f"local home-directory path found in {relative}")
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"possible {label} in {relative}")


def inspect_pdfs(files: list[Path], errors: list[str]) -> None:
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() != ".pdf" or relative in TEMPLATE_PDFS:
            continue
        if relative not in APPROVED_PUBLIC_PDFS:
            errors.append(f"PDF has not received manual privacy approval: {relative}")

    site_root = ROOT / "_site"
    if site_root.exists():
        deployed = {
            path.relative_to(site_root).as_posix()
            for path in site_root.rglob("*.pdf")
        }
        unexpected = deployed - APPROVED_PUBLIC_PDFS
        for relative in sorted(unexpected):
            errors.append(f"unexpected PDF in generated site: {relative}")


def inspect_sensitive_filenames(files: list[Path], errors: list[str]) -> None:
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if SENSITIVE_FILENAMES.search(relative):
            errors.append(f"sensitive-looking filename in repository: {relative}")


def inspect_image_metadata(errors: list[str], warnings: list[str]) -> int:
    image_root = ROOT / "images"
    images = [
        path
        for path in image_root.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    for directory in PUBLIC_IMAGE_ROOTS:
        if directory.exists():
            images.extend(
                path
                for path in directory.rglob("*")
                if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            )

    checked = 0
    try:
        subprocess.run(["sips", "--version"], capture_output=True, check=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        warnings.append("image metadata was not checked because macOS 'sips' is unavailable")
        return checked

    for path in sorted(set(images)):
        if not path.exists():
            continue
        checked += 1
        result = subprocess.run(
            ["sips", "-g", "creation", "-g", "make", "-g", "model", str(path)],
            capture_output=True,
            check=False,
            text=True,
        )
        metadata = {
            key: value
            for key, value in re.findall(r"^\s+(creation|make|model):\s*(.+)$", result.stdout, re.MULTILINE)
            if value != "<nil>"
        }
        if metadata:
            relative = path.relative_to(ROOT).as_posix()
            errors.append(f"photo metadata should be removed from {relative}: {metadata}")
    return checked


def main() -> int:
    files = repo_files()
    errors: list[str] = []
    warnings: list[str] = []

    for path in files:
        inspect_text(path, errors)
    inspect_sensitive_filenames(files, errors)
    inspect_pdfs(files, errors)
    image_count = inspect_image_metadata(errors, warnings)

    print("Pre-publish privacy audit")
    print(f"  Repository files inspected: {len(files)}")
    print(f"  Public PDFs approved: {len(APPROVED_PUBLIC_PDFS)}")
    print(f"  Public images checked for camera/date metadata: {image_count}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        print("FAIL")
        for error in sorted(set(errors)):
            print(f"  - {error}")
        return 1
    print("PASS: no unapproved privacy-sensitive material was detected")
    print("Manual reminder: read every new PDF and inspect every new photograph before adding it to the approval lists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
