#!/usr/bin/env python3
"""Transcripts that Graph will not hand over, read from the recording file in SharePoint.

A channel meeting (thread.tacv2) stores its recording and transcript in the team's SharePoint
site, and the onlineMeetings transcript routes return nothing for it. The transcript is still
reachable as a property of the recording .mp4, but only through the SharePoint host:

  GET https://<tenant>.sharepoint.com/sites/<site>/_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts

Measured once on a real channel meeting: the same path on graph.microsoft.com returns 400, and
calling streamContent directly returns 406. Each transcript in the answer carries a
temporaryDownloadUrl with a tempauth token that expires, so `download` fetches it in the same
run that listed it instead of printing it for later.

  parse     recap link -> driveId, driveItemId, siteUrl (no network)
  find      siteUrl -> the "... Meeting Recording.mp4" files in that site, newest first
  list      recording -> its transcripts with languageTag, read BEFORE downloading
  download  recording -> one transcript saved as .vtt, warns when languageTag is not expected
"""
import argparse
import json
import subprocess
import sys
import urllib.request
from urllib.parse import parse_qs, quote, unquote, urlparse

SITE_ROOTS = ("sites", "teams", "personal")


def parse_recap(url):
    """Teams 'meetingrecap' link -> the ids the SharePoint route needs. Read by parameter
    name, never by position: Teams reorders and adds parameters between versions."""
    q = {k.lower(): v[0] for k, v in parse_qs(urlparse(url).query).items()}
    drive, item = q.get("driveid"), q.get("driveitemid")
    if not drive or not item:
        raise ValueError("link carries no driveId/driveItemId; is it a meetingrecap link?")
    file_url = q.get("sitepath") or q.get("fileurl") or ""
    thread = q.get("threadid") or ""
    return {"driveId": drive, "driveItemId": item, "siteUrl": site_url(file_url),
            "fileUrl": unquote(file_url), "threadId": thread,
            "isChannel": "thread.tacv2" in thread}


def site_url(file_url):
    """https://t.sharepoint.com/sites/X/Shared Documents/a.mp4 -> https://t.sharepoint.com/sites/X"""
    if not file_url:
        return None
    u = urlparse(unquote(unquote(file_url)))
    parts = [p for p in u.path.split("/") if p]
    base = f"{u.scheme}://{u.netloc}"
    return f"{base}/{parts[0]}/{parts[1]}" if len(parts) >= 2 and parts[0] in SITE_ROOTS else base


def m365_json(url):
    out = subprocess.run(["m365", "request", "--url", url, "-o", "json"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"m365 request failed for {url}\n{out.stderr.strip() or out.stdout.strip()}\n"
                         "Rerun the same call with --debug to see Graph's error body.")
    return json.loads(out.stdout or "null")


def _items(data):
    return data.get("value", []) if isinstance(data, dict) else (data or [])


def _get(d, key):
    """The v2.1 payload is not documented; accept any casing of a key."""
    return next((v for k, v in d.items() if k.lower() == key.lower()), None)


def list_transcripts(site, drive, item):
    url = f"{site.rstrip('/')}/_api/v2.1/drives/{quote(drive, safe='')}/items/{quote(item, safe='')}/media/transcripts"
    return [{"id": _get(t, "id"), "languageTag": _get(t, "languageTag"),
             "displayName": _get(t, "displayName"),
             "createdDateTime": _get(t, "createdDateTime"),
             "_url": _get(t, "temporaryDownloadUrl")} for t in _items(m365_json(url))]


def find_recordings(site):
    u = urlparse(site)
    meta = m365_json(f"https://graph.microsoft.com/v1.0/sites/{u.netloc}:{u.path or '/'}?$select=id")
    hits = _items(m365_json(
        f"https://graph.microsoft.com/v1.0/sites/{meta['id']}/drive/root/search(q='Meeting Recording')"
        "?$select=name,id,size,createdDateTime,parentReference,webUrl&$top=200"))
    rows = [{"name": h["name"], "driveId": h["parentReference"]["driveId"], "driveItemId": h["id"],
             "createdDateTime": h.get("createdDateTime"), "sizeMB": round((h.get("size") or 0) / 2**20, 1),
             "folder": (h["parentReference"].get("path") or "").split("root:")[-1]}
            for h in hits if h.get("name", "").lower().endswith(".mp4")]
    return sorted(rows, key=lambda r: r["createdDateTime"] or "", reverse=True)


def lang_matches(tag, expect):
    return (tag or "").lower().split("-")[0] == expect.lower().split("-")[0]


def target(args):
    if args.recap_url:
        r = parse_recap(args.recap_url)
        site = args.site_url or r["siteUrl"]
        if not site:
            raise SystemExit("recap link carries no sitePath; pass --site-url")
        return site, r["driveId"], r["driveItemId"]
    if not (args.site_url and args.drive_id and args.item_id):
        raise SystemExit("give --recap-url, or all of --site-url --drive-id --item-id")
    return args.site_url, args.drive_id, args.item_id


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("parse").add_argument("--recap-url", required=True)
    sub.add_parser("find").add_argument("--site-url", required=True)
    for name in ("list", "download"):
        p = sub.add_parser(name)
        p.add_argument("--recap-url")
        p.add_argument("--site-url", help="https://<tenant>.sharepoint.com/sites/<site>")
        p.add_argument("--drive-id")
        p.add_argument("--item-id", help="driveItemId of the recording .mp4")
        p.add_argument("--expect-lang", default="vi-VN", help="language of the meeting, default vi-VN")
        if name == "download":
            p.add_argument("--transcript-id", help="required when the recording has several")
            p.add_argument("--output", required=True, help="where to write the .vtt")
    args = ap.parse_args()

    if args.cmd == "parse":
        print(json.dumps(parse_recap(args.recap_url), ensure_ascii=False, indent=2))
        return
    if args.cmd == "find":
        print(json.dumps(find_recordings(args.site_url), ensure_ascii=False, indent=2))
        return

    rows = list_transcripts(*target(args))
    for r in rows:
        if not lang_matches(r["languageTag"], args.expect_lang):
            print(f"WARNING: transcript {r['id']} is {r['languageTag']}, the meeting is expected in "
                  f"{args.expect_lang}. Teams transcribed it in the wrong language; expect garbage.",
                  file=sys.stderr)
    if args.cmd == "list":
        print(json.dumps([{k: v for k, v in r.items() if k != "_url"} for r in rows],
                         ensure_ascii=False, indent=2))
        if not rows:
            print("No transcript on this recording. Transcription was off; the .mp4 itself is the "
                  "only source left.", file=sys.stderr)
        return

    pick = [r for r in rows if r["id"] == args.transcript_id] if args.transcript_id else rows
    if len(pick) != 1:
        raise SystemExit(f"{len(pick)} transcripts match; pass --transcript-id, one of: "
                         + ", ".join(f"{r['id']} ({r['languageTag']})" for r in rows))
    if not pick[0]["_url"]:
        raise SystemExit("transcript has no temporaryDownloadUrl in the answer")
    # The tempauth link expires within minutes, which is why it is fetched here and never printed.
    with urllib.request.urlopen(pick[0]["_url"], timeout=120) as resp, open(args.output, "wb") as fh:
        fh.write(resp.read())
    print(json.dumps({k: v for k, v in pick[0].items() if k != "_url"} | {"output": args.output},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
