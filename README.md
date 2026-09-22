# wdgwars-upload-check

Your upload finished and [WDGWars](https://wdgwars.pl) said **0 new APs**. This tells you why.

It reads your own account and answers the two questions that explain almost every zero:

1. **Did this exact file already go up once?** A second upload of a file the server already has is all duplicates and zero new. That is the correct answer, not a fault.
2. **Was your 24 hour new-AP allowance already spent?** Over-cap new APs are skipped quietly, with no error. It looks identical to a parse failure.

It only reads. Nothing is uploaded, nothing is changed, nothing is sent anywhere except to wdgwars.pl. Your API key stays on your machine and is never printed.

## Quick start

**1. Get Python**, if you do not have it. [python.org/downloads](https://www.python.org/downloads/) — on Windows, tick **"Add python.exe to PATH"** in the installer. Any version 3.8 or newer works.

**2. Download this folder.** Click the green **Code** button above, then **Download ZIP**, and unzip it somewhere you can find again.

**3. Get your API key.** Go to [wdgwars.pl/profile](https://wdgwars.pl/profile) and log in. Scroll down to **API Keys**. Either copy a key you already have, or click **Generate new** to make one. The key is shown only once when generated, so copy it before you leave the page.

**4. Run it.**

**Windows.** Open the folder holding the script. Hold **Shift**, right-click an empty part of the folder, and choose **Open PowerShell window here** (older Windows says "Open command window here"). Then type:

```
py -3 wdgwars_upload_check.py
```

and press Enter. If `py` is not recognised, use `python wdgwars_upload_check.py` instead.

**Mac or Linux.** Open a terminal in the folder and run:

```
python3 wdgwars_upload_check.py
```

or `./run.sh`, which does the same thing.

**5. Paste your key when it asks.** The first run stops and asks for it. Paste, press Enter, and it saves the key to `key.txt` next to the script so you are never asked again. Then it runs.

That is it. No pip, no install, no dependencies.

## Removing it

```
python wdgwars_upload_check.py --forget
```

deletes the saved `key.txt`. Deleting the folder removes the tool completely, since it installs nothing anywhere else. Neither of those touches your account, so if you want the key itself retired, revoke it at [wdgwars.pl/profile](https://wdgwars.pl/profile) under API Keys.

## What you will see

```
WDGWars upload check for YourName

== DAILY NEW-AP HEADROOM ==
  used      0
  remaining 500,000
  cap       500,000 per 24h_rolling
  >> headroom available, the cap does not explain a zero-new result

== UPLOAD HISTORY (newest 10) ==

  [1] 2026-09-22 14:16:09.638475+00
      file     my_wardrive_20260917.csv  (40,837,152 bytes)
      via      upload-csv   status done
      imported=308864  captured=3392  updated=30  duplicates=134753  cooldown=55  cap_hits=0

== VERDICT ==
  No file in this window was uploaded twice, so a repeat upload does not
  explain a zero-new result.
```

Read the verdict first. If it names your file as uploaded twice, the earlier one took the data and the zero is correct. If headroom says the cap is spent, that is your answer. If neither, the numbers above are what to bring to the Discord when you ask.

## Options

| Flag | What it does |
|---|---|
| `--limit N` | How many past uploads to fetch, 1 to 50. Default 10. Use `--limit 50` if your upload was a while ago. |
| `--key-file PATH` | Read the key from somewhere other than `key.txt`. |
| `--json` | Dump the two raw API responses instead of the report. For when you want to read the fields yourself. |
| `--forget` | Delete the saved `key.txt` and exit. |

You can also set the key as an environment variable instead of using `key.txt`:

```
set WDGWARS_API_KEY=yourkey
```

on Windows, or

```
export WDGWARS_API_KEY=yourkey
```

on Mac and Linux.

## About your API key

Your key is your account. Treat it like a password.

- This script never prints it and never sends it anywhere except wdgwars.pl.
- It is saved to `key.txt` beside the script, and nowhere else. On Mac and Linux that file is created readable only by you.
- `key.txt` is in `.gitignore`, so it cannot be committed by accident.
- `--forget` deletes it whenever you want.
- Nobody, including whoever is helping you in Discord, needs your key to help you. Run this yourself and share the **output**. If a tool or a person asks you to hand over the key itself, that is the moment to stop and ask in the server first.
- Revoke and regenerate any key you are unsure about, at [wdgwars.pl/profile](https://wdgwars.pl/profile).

## What it actually calls

Two read-only endpoints, both with your key in an `X-API-Key` header:

- `GET /endpoint/me` for `new_ap_limit`, the 24 hour new-AP counter.
- `GET /endpoint/upload-history?limit=N` for your recent uploads and each one's parser result block.

It backs off and retries when the server rate limits it, using the `retry_after` value the server returns.

## Things worth knowing before you blame the parser

- **Re-scans are not new APs.** Driving the same streets again reinforces what you own. It counts for you, it just is not "new".
- **The 24 hour cap is 500,000 new APs**, rolling. Past it, further new APs are skipped silently.
- **One upload should cover about 1,000 km or less.** A long cross-country run is better split by region.
- **Do not split a file yourself.** The server splits oversized files for you and keeps the header on every part. A hand-split file loses its header on every part after the first, and a headerless file is a known way to get your upload misread.
- **A `.gz` is judged on its uncompressed size**, not the size of the archive.

## Not affiliated with LOCOSP

WDGWars is theirs. This is a community-maintained diagnostic. If it says something the site disagrees with, the site is right.

## License

[MIT](LICENSE). Use freely, no warranty.
