#!/usr/bin/env python3
"""Join Teams transcripts to the calendar events they belong to.

A transcript from Graph carries no meeting name, only a `meetingId`. That id is base64 of
`1*{organizerOid}*0**{threadId}`, and the same `threadId` sits inside the join URL of every
calendar event for that meeting. Decoding one side and parsing the other is what turns
"transcript ktVi..." into "[SEKISAN] MONTHLY REPORT, 15 Sep 13:30".

A recurring series shares ONE threadId across every occurrence, so the thread alone cannot
say which Tuesday you meant. The occurrence is decided by time: the event whose start sits
closest to when the transcript began. Comparing formatted dates instead would pick the wrong
meeting whenever a session crosses UTC midnight, which in GMT+7 is any meeting after 07:00.

  match       transcripts + events -> matched rows (the main job)
  meeting-id  join URL -> the meetingId needed to read an attended meeting's transcripts
  decode      meetingId -> organizer oid + threadId
"""
import argparse
import base64
import json
import re
import sys
from datetime import datetime, timedelta, timezone

GMT7 = timezone(timedelta(hours=7))
# Graph returns naive local times when the request carried a Prefer header. Matching on the
# wrong zone is a silent 7-hour error, so only zones we can convert exactly are accepted.
ZONES = {"UTC": 0, "": 0, "SE Asia Standard Time": 7, "Asia/Bangkok": 7, "Asia/Ho_Chi_Minh": 7}
MEETING_ID_RE = re.compile(r"^1\*([0-9a-fA-F-]{36})\*0\*\*(.+)$")


def decode_meeting_id(mid):
    raw = base64.b64decode(mid + "=" * (-len(mid) % 4)).decode("utf-8", "replace")
    m = MEETING_ID_RE.match(raw)
    if not m:
        raise ValueError(f"meetingId does not have the expected 1*oid*0**thread shape: {raw!r}")
    return m.group(1), m.group(2)


def build_meeting_id(oid, thread_id):
    return base64.b64encode(f"1*{oid}*0**{thread_id}".encode()).decode()


def parse_join_url(url):
    """Pull (organizerOid, threadId) out of a Teams join URL, encoded or not."""
    from urllib.parse import unquote
    plain = unquote(unquote(url))
    thread = re.search(r"/l/meetup-join/([^/?]+)", plain)
    oid = re.search(r'"Oid"\s*:\s*"([^"]+)"', plain)
    if not thread or not oid:
        raise ValueError("join URL carries no meetup-join thread id or no Oid in its context")
    return oid.group(1), thread.group(1)


def _utc(value, zone_name):
    txt = re.sub(r"(\.\d{6})\d+", r"\1", (value or "").strip()).replace("Z", "+00:00")
    dt = datetime.fromisoformat(txt)
    if dt.tzinfo is None:
        zone = (zone_name or "").strip()
        if zone not in ZONES:
            raise SystemExit(
                f"Event time '{value}' has no offset and timeZone '{zone}' is not one this script can "
                "convert. Re-read calendarView WITHOUT the Prefer header so Graph returns UTC.")
        dt = dt.replace(tzinfo=timezone(timedelta(hours=ZONES[zone])))
    return dt.astimezone(timezone.utc)


def _items(path):
    data = json.load(open(path, encoding="utf-8"))
    return data.get("value", data) if isinstance(data, dict) else data


def index_events(events):
    """threadId -> occurrences. Channel meetings (thread.tacv2) are kept so the caller can
    explain why they have no transcript, rather than reporting a puzzling no-match."""
    by_thread = {}
    for ev in events:
        url = ((ev.get("onlineMeeting") or {}).get("joinUrl")) or ev.get("joinWebUrl")
        if not url:
            continue
        try:
            oid, thread = parse_join_url(url)
        except ValueError:
            continue
        start = ev.get("start") or {}
        by_thread.setdefault(thread, []).append({
            "subject": ev.get("subject"), "organizerOid": oid,
            "startUtc": _utc(start.get("dateTime"), start.get("timeZone")),
            "organizer": ((ev.get("organizer") or {}).get("emailAddress") or {}).get("name"),
            "organizerEmail": ((ev.get("organizer") or {}).get("emailAddress") or {}).get("address"),
            "isChannel": "thread.tacv2" in thread,
        })
    return by_thread


def match(transcripts, events, tolerance_min=240, start=None, end=None, me=None):
    by_thread = index_events(events)
    rows = []
    for tr in transcripts:
        created = _utc(tr.get("createdDateTime"), "UTC")
        if (start and created < start) or (end and created >= end):
            continue
        try:
            organizer_oid, thread = decode_meeting_id(tr.get("meetingId", ""))
        except (ValueError, Exception):
            organizer_oid, thread = None, None
        row = {
            "transcriptId": tr.get("id"), "meetingId": tr.get("meetingId"),
            "threadId": thread, "organizerOid": organizer_oid,
            "createdUtc": created.isoformat(), "startedLocal": created.astimezone(GMT7).strftime("%Y-%m-%d %H:%M"),
            "endedUtc": tr.get("endDateTime"), "subject": None, "matched": False,
            # Which route reached this transcript decides what else is available: attendance
            # and recordings exist only for meetings you organized.
            "role": None if not me else ("organizer" if organizer_oid == me else "attendee"),
        }
        best = min(by_thread.get(thread, []), key=lambda e: abs(e["startUtc"] - created), default=None)
        if best:
            gap = abs(best["startUtc"] - created).total_seconds() / 60
            row["gapMinutes"] = round(gap, 1)
            row["isChannelMeeting"] = best["isChannel"]
            if gap <= tolerance_min:
                row.update(matched=True, subject=best["subject"], organizer=best["organizer"],
                           organizerEmail=best["organizerEmail"],
                           eventStartUtc=best["startUtc"].isoformat(),
                           eventStartLocal=best["startUtc"].astimezone(GMT7).strftime("%Y-%m-%d %H:%M"))
        rows.append(row)
    rows.sort(key=lambda r: r["createdUtc"], reverse=True)
    return rows


def attended(events, me, include_channel=False):
    """Threads of meetings someone else organized, deduped, newest subject order.

    There is no bulk endpoint for meetings you merely attended, so each one costs a Graph call.
    Deduping by thread is what keeps that affordable: `/onlineMeetings/{id}/transcripts` returns
    every occurrence of a series, so a daily standup is one call for the week rather than five.
    """
    rows = []
    for thread, occurrences in index_events(events).items():
        first = occurrences[0]
        if (first["isChannel"] and not include_channel) or first["organizerOid"] == me:
            continue
        rows.append({
            "threadId": thread, "meetingId": build_meeting_id(first["organizerOid"], thread),
            "organizerOid": first["organizerOid"], "subject": first["subject"],
            "organizer": first["organizer"], "occurrences": len(occurrences),
            "isChannel": first["isChannel"],
        })
    return sorted(rows, key=lambda r: (r["subject"] or ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("match", help="join transcripts to calendar events")
    m.add_argument("--transcripts", required=True)
    m.add_argument("--events", required=True)
    m.add_argument("--from", dest="start", help="ISO instant, drop transcripts started earlier")
    m.add_argument("--to", dest="end", help="ISO instant, exclusive")
    m.add_argument("--tolerance-min", type=float, default=240,
                   help="reject a pairing further apart than this, default 240")
    m.add_argument("--me", help="your own object id, stamps each row organizer or attendee")
    a = sub.add_parser("attended", help="threads organized by other people, one row per thread")
    a.add_argument("--events", required=True)
    a.add_argument("--me", required=True)
    a.add_argument("--include-channel", action="store_true",
                   help="also list channel threads, which only the SharePoint route can read")
    b = sub.add_parser("meeting-id", help="join URL -> meetingId for the transcripts endpoint")
    b.add_argument("--join-url", required=True)
    d = sub.add_parser("decode", help="meetingId -> organizer oid and threadId")
    d.add_argument("--meeting-id", required=True)
    args = ap.parse_args()

    if args.cmd == "meeting-id":
        oid, thread = parse_join_url(args.join_url)
        print(build_meeting_id(oid, thread))
    elif args.cmd == "decode":
        oid, thread = decode_meeting_id(args.meeting_id)
        print(json.dumps({"organizerOid": oid, "threadId": thread}, ensure_ascii=False))
    elif args.cmd == "attended":
        print(json.dumps(attended(_items(args.events), args.me, args.include_channel), ensure_ascii=False, indent=2))
    else:
        rows = match(_items(args.transcripts), _items(args.events), args.tolerance_min,
                     _utc(args.start, "UTC") if args.start else None,
                     _utc(args.end, "UTC") if args.end else None, args.me)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        if not any(r["matched"] for r in rows) and rows:
            print("No transcript matched a calendar event. Widen the calendarView window: an "
                  "occurrence outside it cannot be matched.", file=sys.stderr)


if __name__ == "__main__":
    main()
