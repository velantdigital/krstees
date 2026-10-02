#!/usr/bin/env python3
"""
Pre-deploy checklist for krs-tees-order (v9).
Run this from inside the v9 folder, EVERY TIME, before dragging it onto Vercel:

    python3 verify-deploy.py

Exits non-zero (and prints what's wrong) if anything looks unsafe to ship.
Catches the exact categories of bug that have broken this site before:
duplicate DOM ids, JS syntax errors, order.html/index.html drifting apart,
a missing image reference, and SITE_BUILD_ID/version.json getting out of sync.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
problems = []
warnings = []

# 1. order.html and index.html must be byte-identical (Vercel serves index.html)
order_html = (ROOT / "order.html")
index_html = (ROOT / "index.html")
if not order_html.exists():
    problems.append("order.html is missing")
if not index_html.exists():
    problems.append("index.html is missing")
if order_html.exists() and index_html.exists():
    if order_html.read_bytes() != index_html.read_bytes():
        problems.append("order.html and index.html are NOT identical — index.html is what Vercel actually serves, so this means the live site will NOT match what you think you're shipping. Copy order.html over index.html.")

content = order_html.read_text(encoding="utf-8") if order_html.exists() else ""

# 2. No duplicate element ids (breaks getElementById-based JS in unpredictable ways)
ids = re.findall(r'id="([^"]+)"', content)
dupes = {k: v for k, v in Counter(ids).items() if v > 1}
if dupes:
    problems.append(f"duplicate element id(s) found: {dupes}")

# 3. Every inline <script> block must be syntactically valid JS
blocks = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', content, re.S)
js_blocks = [b for b in blocks if b.strip() and "src=" not in b[:0]]  # inline only (already excludes external via the regex not matching self-closing)
check_file = ROOT / ".verify_check.js"
check_file.write_text("\n".join(f"// block {i}\n{b}" for i, b in enumerate(js_blocks)), encoding="utf-8")
result = subprocess.run(["node", "--check", str(check_file)], capture_output=True, text=True)
check_file.unlink(missing_ok=True)
if result.returncode != 0:
    problems.append(f"JS syntax error in an inline <script> block:\n{result.stderr.strip()}")

# 4. SITE_BUILD_ID (in the page) must match version.json — this is what stops the
#    stale-browser-cache bug that once caused a real order to go out with no sales tax.
build_id_match = re.search(r"const SITE_BUILD_ID = '([^']+)'", content)
version_json = ROOT / "version.json"
if build_id_match and version_json.exists():
    import json
    vjson_build = json.loads(version_json.read_text()).get("build")
    if build_id_match.group(1) != vjson_build:
        problems.append(f"SITE_BUILD_ID in the page ('{build_id_match.group(1)}') does not match version.json ('{vjson_build}') — bump both together or returning visitors can get served stale pricing/products.")
elif not build_id_match:
    problems.append("Could not find SITE_BUILD_ID in order.html")
elif not version_json.exists():
    problems.append("version.json is missing")

# 5. Every local image/asset referenced in the page should actually exist on disk
img_refs = set(re.findall(r'''(?:src|img)\s*[:=]\s*['"]((?:images|favicon)[^'"]+)['"]''', content))
for ref in sorted(img_refs):
    if not (ROOT / ref).exists():
        # Not blocking: the page registers a global window "error" listener in <head>
        # that swaps in a "Photo coming soon" placeholder for any failed image load,
        # so a missing photo degrades gracefully instead of breaking the page. Still
        # worth knowing about so it gets a real photo eventually.
        warnings.append(f"referenced image/file does not exist on disk (will show the 'Photo coming soon' placeholder, not break): {ref}")

# 6. Nothing private should be sitting inside this folder (Vercel drag-and-drop
#    uploads EVERY file here, with no .vercelignore support) — this is exactly
#    how the Orders Hub secret key leaked publicly once before.
sensitive_patterns = ["Code.gs", "README-ORDERS-HUB.md", ".bak", ".env"]
for p in ROOT.rglob("*"):
    if p.is_file() and any(s in p.name for s in sensitive_patterns):
        problems.append(f"sensitive/private file sitting inside the deploy folder — this WILL be uploaded publicly: {p.relative_to(ROOT)}")

# 7. Orders Hub webhook key must be present (warn only — site works without it)
if 'ORDER_HUB_WEBHOOK_URL = ""' in content or "ORDER_HUB_WEBHOOK_URL = ''" in content:
    warnings.append("ORDER_HUB_WEBHOOK_URL is blank — orders will process fine but nothing will log to your Orders Hub sheet.")

print("=" * 60)
if problems:
    print(f"❌ {len(problems)} problem(s) — DO NOT DEPLOY until these are fixed:\n")
    for i, p in enumerate(problems, 1):
        print(f"{i}. {p}\n")
else:
    print("✅ All checks passed — safe to drag this v9 folder onto Vercel.")
if warnings:
    print(f"\n⚠ {len(warnings)} warning(s) (not blocking):\n")
    for w in warnings:
        print(f"- {w}")
print("=" * 60)
sys.exit(1 if problems else 0)
