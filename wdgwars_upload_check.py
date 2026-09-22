#!/usr/bin/env python3
"""Check your own WDGWars upload history and daily new-AP headroom.

Answers two questions when an upload reports zero new APs:

  1. Did the same capture already go up once? A second upload of a file the
     server already has is all duplicates and zero new, which is correct
     rather than broken.
  2. Was the 24h new-AP cap already spent? Over-cap new APs are skipped
     silently with no error, which looks identical to a parse failure.

Reads only. Nothing is uploaded, changed or sent anywhere. Your key stays on
your machine and is never printed.

Usage:
    set WDGWARS_API_KEY=...          (Windows)
    export WDGWARS_API_KEY=...       (macOS / Linux)
    python wdgwars_upload_check.py

    python wdgwars_upload_check.py --limit 50
    python wdgwars_upload_check.py --key-file ~/.config/wdgwars/key
    python wdgwars_upload_check.py --json

Get your key from https://wdgwars.pl/profile under API Keys.
"""

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

BASE = "https://wdgwars.pl/endpoint"
UA = "wdgwars-upload-check/1.0"
MAX_RETRIES = 4


NO_KEY = """
No API key found. Pick whichever of these is easiest.

  1. Put your key in a file called key.txt next to this script.
     That is all. Run it again.

  2. Or set an environment variable:
       Windows      set WDGWARS_API_KEY=yourkey
       Mac / Linux  export WDGWARS_API_KEY=yourkey

  3. Or point at a file yourself:
       python wdgwars_upload_check.py --key-file path/to/key

Get a key from https://wdgwars.pl/profile, under API Keys, by clicking
"Generate new". The key is shown once, so copy it before leaving the page.
""".strip()


def _from_file(path, required):
    try:
        with open(path, encoding="utf-8") as fh:
            key = fh.read().strip()
    except OSError as exc:
        if required:
            sys.exit("cannot read key file %s: %s" % (path, exc))
        return ""
    if key or not required:
        return key
    sys.exit("key file %s is empty" % path)


def read_key(args):
    if args.key_file:
        return _from_file(os.path.expanduser(args.key_file), True)

    key = (os.environ.get("WDGWARS_API_KEY") or "").strip()
    if key:
        return key

    # key.txt beside the script, then beside the shell's working directory
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, "key.txt"), os.path.abspath("key.txt")):
        key = _from_file(path, False)
        if key:
            return key

    sys.exit(NO_KEY)


def get(path, key):
    """GET one endpoint, backing off on 429 using the body's retry_after."""
    req = urllib.request.Request(
        BASE + path,
        headers={"X-API-Key": key, "User-Agent": UA, "Accept": "application/json"},
    )
    ctx = ssl.create_default_context()
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            if exc.code == 429:
                wait = 30
                try:
                    wait = int(json.loads(body).get("retry_after", 30))
                except (ValueError, TypeError, AttributeError):
                    pass
                if attempt == MAX_RETRIES - 1:
                    sys.exit("rate limited and out of retries")
                print("  rate limited, waiting %ds" % wait, file=sys.stderr)
                time.sleep(wait)
                continue
            if exc.code == 401:
                sys.exit("401 from %s: the key was rejected. Check it is the "
                         "full key and has not been revoked." % path)
            sys.exit("HTTP %d from %s: %s" % (exc.code, path, body[:300]))
        except urllib.error.URLError as exc:
            sys.exit("cannot reach wdgwars.pl%s: %s" % (path, exc.reason))
    sys.exit("gave up on %s" % path)


def fmt(n):
    return "{:,}".format(n) if isinstance(n, int) else str(n)


def show_headroom(me):
    lim = me.get("new_ap_limit")
    print("== DAILY NEW-AP HEADROOM ==")
    if not isinstance(lim, dict):
        print("  not reported by this account, check the HEADROOM tile on "
              "https://wdgwars.pl/uplink instead")
        print()
        return
    used = lim.get("used")
    cap = lim.get("cap")
    print("  used      %s" % fmt(used))
    print("  remaining %s" % fmt(lim.get("remaining")))
    print("  cap       %s per %s" % (fmt(cap), lim.get("window", "24h")))
    if isinstance(used, int) and isinstance(cap, int) and cap and used >= cap:
        print("  >> CAP IS SPENT. New APs are being skipped silently. This "
              "alone explains a zero-new result.")
    else:
        print("  >> headroom available, the cap does not explain a zero-new "
              "result")
    print()


# Counters worth showing per upload. `total` is deliberately excluded: it is
# the platform-wide network count, not yours, and it moves on every upload.
COUNTERS = ("imported", "captured", "updated", "duplicates", "cooldown",
            "cap_hits", "no_gps", "bad_rows")


def show_history(hist, limit):
    uploads = hist.get("uploads") or hist.get("history") or hist.get("items")
    if uploads is None and isinstance(hist.get("data"), list):
        uploads = hist["data"]
    if not uploads:
        print("== UPLOAD HISTORY ==")
        print("  no uploads returned")
        print()
        return

    print("== UPLOAD HISTORY (newest %d) ==" % min(limit, len(uploads)))
    by_file = {}
    capped = []
    for i, up in enumerate(uploads, 1):
        when = up.get("created_at") or up.get("when") or up.get("time") or "?"
        name = up.get("filename") or "(unnamed)"
        size = up.get("file_size")
        res = up.get("result")
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except ValueError:
                res = {}
        if not isinstance(res, dict):
            res = {}

        print("\n  [%d] %s" % (i, when))
        print("      file     %s%s" % (
            name, "  (%s bytes)" % fmt(size) if size is not None else ""))
        print("      via      %s   status %s" % (
            up.get("endpoint", "?"), up.get("status", "?")))
        shown = [(k, res[k]) for k in COUNTERS if k in res]
        if shown:
            print("      " + "  ".join("%s=%s" % (k, fmt(v)) for k, v in shown))
        else:
            print("      (no counters in result block)")

        if res.get("cap_hits"):
            capped.append(i)

        # Same filename AND same byte count is the same file, sent twice.
        if size is not None and name != "(unnamed)":
            by_file.setdefault((name, size), []).append(i)

    repeats = {k: v for k, v in by_file.items() if len(v) > 1}
    print("\n== VERDICT ==")
    if repeats:
        print("  The same file appears more than once in this window:")
        for (name, size), idxs in repeats.items():
            print("    %s (%s bytes) as entries %s" % (
                name, fmt(size), ", ".join("[%d]" % i for i in idxs)))
        print("  The earliest of each pair took the data. A later upload of "
              "the same file is all duplicates and zero new, which is the "
              "correct answer rather than a fault.")
    else:
        print("  No file in this window was uploaded twice, so a repeat "
              "upload does not explain a zero-new result.")
    if capped:
        print("  Entries %s recorded cap_hits, meaning new APs were skipped "
              "against the 24h cap." % ", ".join("[%d]" % i for i in capped))
    print("  Widen the window with --limit 50 if your upload is older than "
          "what is shown.")
    print()


def main():
    ap = argparse.ArgumentParser(
        description="Check your own WDGWars upload history and new-AP headroom.")
    ap.add_argument("--limit", type=int, default=10,
                    help="uploads to fetch, 1 to 50 (default 10)")
    ap.add_argument("--key-file", help="file holding the API key")
    ap.add_argument("--json", action="store_true",
                    help="dump both raw responses instead of a report")
    args = ap.parse_args()

    if not 1 <= args.limit <= 50:
        sys.exit("--limit must be between 1 and 50")

    key = read_key(args)
    me = get("/me", key)
    hist = get("/upload-history?limit=%d" % args.limit, key)

    if args.json:
        json.dump({"me": me, "upload_history": hist}, sys.stdout, indent=2)
        print()
        return

    print()
    print("WDGWars upload check for %s" % (me.get("username") or "your account"))
    print()
    show_headroom(me)
    show_history(hist, args.limit)


if __name__ == "__main__":
    main()
