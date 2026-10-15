# Graph recipes and raw evidence

Everything here was run against a live tenant while building the skill. Where Microsoft's
documentation disagrees with what the tenant did, the measurement is recorded and the
documented claim is noted next to it.

## Contents

1. Endpoints
2. How a `meetingId` is built
3. Paging
4. Matching a transcript to a calendar event
5. Transcript content formats
6. Raw evidence behind the pitfall table
7. Where the documentation and the tenant disagree

---

## 1. Endpoints

`{me}` is your own object id from `GET /me?$select=id`. Everything is under `v1.0`.

| Purpose                             | Endpoint                                                                     |
| ----------------------------------- | ----------------------------------------------------------------------------- |
| All transcripts you organized       | `users/{me}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{me}')` |
| Transcripts of one meeting thread   | `users/{me}/onlineMeetings/{meetingId}/transcripts`                          |
| Transcript content, VTT             | `.../transcripts/{id}/content?$format=text/vtt`                              |
| Transcript content, JSON per cue    | `.../transcripts/{id}/metadataContent`                                       |
| All recordings you organized        | `users/{me}/onlineMeetings/getAllRecordings(meetingOrganizerUserId='{me}')`  |
| Attendance reports                  | `users/{me}/onlineMeetings/{meetingId}/attendanceReports`                    |
| Attendance rows                     | `.../attendanceReports/{reportId}/attendanceRecords`                         |
| Lookup by join link                 | `users/{me}/onlineMeetings?$filter=joinWebUrl eq '{url}'`                     |
| Transcripts of a recording file     | `https://<tenant>.sharepoint.com/sites/<site>/_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts` (SharePoint host, not Graph) |

The organizer id is a **function parameter**, not a `$filter`. Writing it as a filter fails.

The join-link lookup needs `OnlineMeetings.Read` and is rarely worth it: building the id from the
link directly (section 2) reaches the same meeting with no extra call and no extra scope.

Percent-encode any id spliced into a URL. Measured ids are base64 containing `=`, `+` and `/`,
and a raw `/` breaks the path:

```bash
ENC=$(jq -rn --arg s "$MEETING_ID" '$s|@uri')
```

## 2. How a `meetingId` is built

A `meetingId` is base64 of a five-field string:

```
1*{organizerObjectId}*0**{threadId}
```

Measured example, decoded:

```
1*11111111-1111-1111-1111-111111111111*0**19:meeting_AAAAweekly@thread.v2
```

Both halves are sitting in the calendar event's join URL, so an attended meeting needs no lookup:

```
https://teams.microsoft.com/l/meetup-join/19%3ameeting_AAAAweekly%40thread.v2/0?context=%7b%22Tid%22%3a%22...%22%2c%22Oid%22%3a%22{organizerObjectId}%22%7d
                                          ^^^^^^ threadId, percent-encoded                        ^^^^^^ organizer, in the context blob
```

`scripts/meeting-resolver.py` does both directions:

```bash
python3 meeting-resolver.py meeting-id --join-url 'https://teams.microsoft.com/l/meetup-join/...'
python3 meeting-resolver.py decode --meeting-id 'MSox...'
```

A join URL whose thread ends in `@thread.tacv2`, usually with a long number where the `0` sits,
is a **channel** meeting. The id builds fine and the endpoint returns nothing useful; the
transcript is reachable from the recording in SharePoint instead, `sharepoint-route.md`.

## 3. Paging

`m365 request` does not follow `@odata.nextLink`, and this endpoint pages in a way that punishes
both obvious mistakes. Use `scripts/list-transcripts.sh`; if you must inline it:

```bash
URL="https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='$ME')"
: > all.ndjson
while [ -n "$URL" ]; do
  m365 request --url "$URL" -o json > page.json
  [ "$(jq '.value|length' page.json)" = 0 ] && break     # the ONLY reliable end
  jq -c '.value[]' page.json >> all.ndjson
  URL=$(jq -r '."@odata.nextLink" // empty' page.json)
done
jq -s '.' all.ndjson
```

Measured: page 1 returned 6 items plus a `nextLink`; page 2 returned 3; pages 3 through 11 each
returned 0 items **and a fresh `nextLink`**. Stopping on a missing link would loop forever;
reading only page 1 would lose a third of the history with no sign anything was missing.

## 4. Matching a transcript to a calendar event

Transcripts carry no subject. The link is the thread id, shared by the `meetingId` and the join URL.

Fetch events **without** `--prefer`, so `start.dateTime` is UTC and `start.timeZone` says `UTC`:

```bash
m365 request --url "https://graph.microsoft.com/v1.0/me/calendarView?startDateTime=$START&endDateTime=$END&\$select=subject,start,organizer,onlineMeeting&\$top=200" -o json > events.json
python3 meeting-resolver.py match --transcripts transcripts.json --events events.json --me "$ME"
```

Why time decides the occurrence, and why on instants: a recurring series reuses one thread id, so
the thread narrows it to "some Tuesday" and no further. Comparing formatted dates instead would
break for any meeting after 07:00 GMT+7, whose UTC timestamp falls on the previous calendar day.

Measured gaps between a scheduled start and the transcript's `createdDateTime`, across six
meetings: 5.0, 5.1, 5.9, 7.8, 9.3, 11.4 minutes. Transcription starts when someone switches it on,
not when the invite says. The default 240-minute tolerance is a rejection threshold, not a
matching window: the nearest occurrence always wins, and the threshold only decides whether the
nearest is close enough to trust.

## 5. Transcript content formats

`?$format=text/vtt` gives the classic shape, one cue per breath:

```
00:00:11.712 --> 00:00:24.712
<v @1>Ok giờ em xin phép bắt đầu buổi họp hôm nay.</v>
```

`metadataContent` is **also a WEBVTT file**, not a JSON document. Each cue payload happens to be a
JSON object, which adds absolute timestamps and the spoken language:

```
00:00:03.712 --> 00:00:04.712
{"startDateTime":"2026-09-15T06:35:03.9164263+00:00","endDateTime":"...","speakerName":"Trần Bảo Ngọc","spokenText":"Trước đây.","spokenLanguage":"vi-vn"}
```

`transcript-to-text.py` detects which one it was handed. VTT is the default because it is smaller
and the relative cue times are what the `.txt` prints anyway; reach for `metadataContent` when you
need wall-clock times per sentence or the per-cue language. The `.docx` format Microsoft used to
offer is gone.

Speakers outside the tenant appear as `@1`, `@2`. That is Teams withholding the name, not a bug,
and not something to paper over with a guess.

## 6. Raw evidence behind the pitfall table

**Date filters accepted and ignored.** Asking for September only:

```bash
m365 request --url "$BULK?startDateTime=2026-09-01T00:00:00Z&endDateTime=2026-09-16T00:00:00Z" \
  -o json --query 'value[].createdDateTime'
# 2026-09-15..., 2026-08-26..., 2026-08-22..., 2026-08-19..., 2026-08-17..., 2026-08-13...
```

`$filter=createdDateTime ge 2026-09-01T00:00:00Z` behaves the same way: 200, full list, no error.
There is no server-side narrowing on this endpoint.

**403 on an invited meeting.** Eleven meetings organized by other people were probed. Three
returned a transcript, seven returned an empty list (no transcription that day), and one returned:

```json
{ "code": "Forbidden", "message": "3003: User does not have access to lookup meeting" }
```

**Reading the app registration needs admin.** `applications?$filter=appId eq '...'` returns 403 for
an ordinary user, so "declared but not consented" cannot be distinguished from "never declared"
from the user's side. Ask IT to add the permissions **and** grant consent in one message.

**`$expand=attendanceRecords` returns null.** The report comes back with the records field empty;
the sub-endpoint returns them.

**Seeing the real error.** `m365 request` prints only the status line on a 4xx and drops the body.
Rerun with `--debug` and grep for `"code"` and `"message"`, as described in `m365-shared`.

## 7. Where the documentation and the tenant disagree

Microsoft documents `getAllTranscripts` and `getAllRecordings` as **application-only**. Both worked
with delegated auth on the measured tenant, on the condition that `meetingOrganizerUserId` is your
own id. Recording **content** does refuse a different organizer, with `userId must match organizerId`.

The two tenant switches that gate all of this are Teams policy, not Graph permissions:

```powershell
Set-CsTeamsMeetingPolicy -Identity Global -EnableGraphTranscriptAccess $true -EnableAttributedTranscripts $true
```

Both default to off. The first exposes transcripts to Graph at all; without the second, Graph
returns transcripts stripped of speaker names. On the measured tenant the change took about four
minutes to reach every Graph front end, and during that window the same call alternated between
200 and 403. That is why `preflight.sh` probes repeatedly instead of trusting one answer. There is
no documented figure for this, so do not promise the user a number.
