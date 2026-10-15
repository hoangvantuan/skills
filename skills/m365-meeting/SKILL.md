---
name: m365-meeting
description: "Teams meeting transcripts via the m365 CLI, Microsoft Graph and SharePoint (channel meetings, meetingrecap links): find the session, check the transcript language and quality, save it as a readable .txt beside the original .vtt, recordings, attendance. Use to fetch a transcript, not summarize one."
allowed-tools:
  - Bash
  - Read
---

# m365-meeting: Teams Transcripts, Recordings, Attendance

Fetch a transcript, write two files, stop. The `.txt` is for a model to read, the `.vtt` is the
untouched original. Summarizing is a different job with a different skill, so do not start one.

## Prerequisites

Run the preflight once at the start of a session. Three different walls all surface as a 403,
and it takes the guesswork out of which one you hit:

```bash
SK="<absolute path of the directory holding this SKILL.md>"   # cwd is usually the project, not the skill
"$SK/scripts/preflight.sh"
```

Exit 0 means go, 2 means partial (say which part is unavailable and carry on), 1 means blocked
and the output already contains the message to forward to IT. If a command fails with a 403
later in the session, rerun with `--full`: a freshly enabled tenant policy propagates gradually
and a single 403 is not a verdict.

Sign in with `m365 login --authType browser`. Never a bare `m365 login`: it defaults to the
device code flow, which private app registrations often disable, and the failure is a bare
`invalid_client` that says nothing about the real cause. Shared auth notes live in
`../m365-shared/references/authentication.md`.

## Operating principles

**A meeting is identified by `(meetingId, start time)`, never by name.** Names are not unique and
a recurring series reuses one `meetingId` for every occurrence. Every entry point (a name plus a
time anchor, a listing, a pasted link) resolves down to that pair before anything is downloaded.

**Three routes, tried in this order.** Who organized the meeting and where it was held decide which
one can see it, and the cheap route only covers half the meetings:

| Route              | Covers                        | How                                                                            | Cost                   |
| ------------------ | ----------------------------- | ------------------------------------------------------------------------------ | ---------------------- |
| bulk               | meetings **you** organized    | `getAllTranscripts(meetingOrganizerUserId='<you>')`, paged                     | one call for all of it |
| per-meeting thread | meetings you **attended**     | build the `meetingId` from the event's join URL, then `/onlineMeetings/{id}/transcripts` | one call per thread    |
| SharePoint         | **channel** meetings (`thread.tacv2`), and any meeting whose recording `.mp4` you can open | the recording's `media/transcripts` on the SharePoint host, section 7 | two or three calls     |

Only after all three come back empty is "there is no transcript" a conclusion. The Graph routes
returning nothing for a channel meeting is not that conclusion: it is the cue to go to SharePoint.

There is no bulk endpoint for meetings other people organized, so the attended route costs a call
per meeting thread. Dedupe by thread before looping: that endpoint returns **every occurrence** of
a series, so a daily standup is one call for the whole week rather than five.

**Graph through `m365 request`, not the native commands.** `m365 teams meeting transcript list`
exists but takes one `--meetingId` at a time with no bulk form, and `transcript get` has no format
flag, so there is no way to ask for VTT. Use Graph for everything here.

**Fetch calendar events for matching WITHOUT the `Prefer` header.** This is the exact opposite of
the rule in `m365-calendar`, and the reason matters: matching happens on instants, and a naive
local timestamp cannot be compared to a transcript's UTC `createdDateTime` without knowing its
zone. No `Prefer` means Graph returns UTC and says so in `start.timeZone`. The resolver accepts
a `SE Asia Standard Time` file too, and refuses any zone it cannot convert exactly rather than
guessing, because guessing here silently selects a neighbouring occurrence.

---

## Pitfalls on the Graph routes

Every row below was measured against a real tenant in this skill's build, **on ordinary (non-channel)
meetings**. None of them has been checked on a channel meeting; the SharePoint route has its own
table in section 7. Most are **silent**: the call succeeds, returns data, and the data is
incomplete or wrong.

| Pitfall                                           | Symptom                                                                                                                                     | Correct approach                                                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `getAllTranscripts` pages, and page one looks whole | measured: page one returned **6** transcripts, following `@odata.nextLink` produced **3 more**. Nothing signals the shortfall                | always page. `scripts/list-transcripts.sh` does it                                                     |
| `while nextLink` never terminates                 | past the end Graph keeps returning a `nextLink` with an **empty** `value` array, forever                                                     | stop on an empty page, not on a missing link                                                           |
| Server-side date filters are accepted and ignored | `?startDateTime=...&endDateTime=...` **and** `$filter=createdDateTime ge ...` both return the full unfiltered list. A September window returned an August 13 transcript | filter client-side with `meeting-resolver.py --from/--to`                                             |
| Transcripts carry no meeting name                 | the payload has `meetingId` and timestamps and nothing human-readable                                                                       | decode the `meetingId` to a thread id and match it to the calendar, see below                          |
| A recurring series shares one `meetingId`         | five weekly occurrences are indistinguishable by id alone                                                                                   | pick the occurrence whose start is nearest the transcript's `createdDateTime`                          |
| Recording starts after the meeting does           | measured gaps between scheduled start and `createdDateTime`: 5.0, 5.1, 5.9, 7.8, 9.3, 11.4 minutes                                          | never require an exact time match; the resolver's default tolerance is 240 minutes and picks the nearest |
| `metadataContent` is not JSON                     | it is a WEBVTT file whose every cue payload happens to be a JSON object                                                                          | feed it to `transcript-to-text.py` like any VTT, it detects the shape                                  |
| `thread.tacv2` in a join URL                      | a **channel** meeting. The Graph transcript routes return nothing for it, with no error                                                     | stop probing Graph and switch to the SharePoint route, section 7                                       |
| `3003: User does not have access to lookup meeting` | a 403 on a meeting that IS on your calendar and that you were invited to                                                                    | not fixable from here. Report it for that meeting and continue with the others                         |
| `$expand=attendanceRecords` returns null          | the report comes back, the records inside are empty                                                                                         | read the `attendanceReports/{id}/attendanceRecords` sub-endpoint instead                               |
| Cues overlap and interleave                       | two people talking at once produce cues whose spans intersect; cue N may not end before cue N+1 starts                                       | already handled by the converter, do not "fix" the ordering                                            |
| Reading the app registration needs admin          | `applications?$filter=appId eq '...'` returns **403** for an ordinary user                                                                  | you cannot tell "not declared" from "declared but not consented", so ask IT for both at once           |

`OnlineMeetingTranscript.Read.All` and `OnlineMeetingRecording.Read.All` are **not** in the `m365
setup` "All" preset, so a fresh install will not have them even after a successful login. The
preflight says so explicitly. Transcript and recording content are also billed under the Teams
meeting API model; the listing calls are not.

---

## 1. Transcripts of meetings you organized

```bash
SK="<absolute path of the skill directory>"
DR="$SK/../m365-calendar/scripts/date-range.sh"     # reused, do not duplicate it
ME=$(m365 request --url 'https://graph.microsoft.com/v1.0/me?$select=id' -o json --query 'id' | tr -d '"')
RANGE=$("$DR" week); START="${RANGE% *}"; END="${RANGE#* }"

"$SK/scripts/list-transcripts.sh" > transcripts.json      # paged for you

# Events for matching: no --prefer, so start.dateTime comes back as UTC
m365 request --url "https://graph.microsoft.com/v1.0/me/calendarView?startDateTime=$START&endDateTime=$END&\$select=subject,start,organizer,onlineMeeting&\$top=200" \
  -o json > events.json

python3 "$SK/scripts/meeting-resolver.py" match \
  --transcripts transcripts.json --events events.json --me "$ME" --from "$START" --to "$END"
```

Each row carries `subject`, `eventStartLocal` (GMT+7, for showing the user), `eventStartUtc` and
`endedUtc` (for the converter), `role`, `meetingId`, `transcriptId`, and `gapMinutes`. Print the
resolved window to the user, the same way `m365-calendar` does, so a different reading of "last
week" is caught immediately.

A row with `matched: false` is a transcript whose meeting is not in the calendar window. Usually
it is an ad-hoc "Meet now", or the window is too narrow. Widen the window before concluding
anything; never attach the nearest name to it as a guess.

## 2. Transcripts of meetings you attended

```bash
python3 "$SK/scripts/meeting-resolver.py" attended --events events.json --me "$ME" > attended.json

jq -r '.[].meetingId' attended.json | while read -r MID; do
  "$SK/scripts/list-transcripts.sh" --meeting-id "$MID"
done | jq -s 'add // []' > attended-transcripts.json
```

Then run the same `match` as section 1 with this file. Some of these calls return 403
(`3003: User does not have access to lookup meeting`) even for meetings you were invited to;
that is a Microsoft-side restriction. Note which meetings it hit and carry on with the rest.

## 3. "What do I have this week?"

Run sections 1 and 2 over the default 7-day window and present one table:

| Date (GMT+7) | Meeting | You are | Transcript |
| ------------ | ------- | ------- | ---------- |

The "no" rows are the meetings with nothing to fetch: events in `events.json` that carry a
`joinUrl` whose thread id appears in no matched row. A `thread.tacv2` thread never surfaces on the
Graph routes even when it was transcribed, so mark those rows `channel, check SharePoint` instead of
"no" (`meeting-resolver.py attended --include-channel` lists them), and offer section 7.

Cost is roughly one bulk call plus one call per attended thread, about 15 calls for a normal week.
For a wider window pass a different anchor to `date-range.sh` (`month`, or two explicit dates);
say which window you used.

## 4. A pasted Teams link

Two kinds of link arrive here. Tell them apart by the path:

- `/l/meetingrecap?...` is the recap link Teams shows after a meeting. It names the recording file
  directly (`driveId`, `driveItemId`, `sitePath`), so go straight to section 7 with `--recap-url`.
  This works for channel meetings and ordinary ones alike.
- `/l/meetup-join/...` is a join URL. If its thread ends in `thread.tacv2`, it is a channel
  meeting: go to section 7 and find the recording by name. Otherwise read on.

A join URL already contains everything needed, so no lookup and no `OnlineMeetings.Read`:

```bash
MID=$(python3 "$SK/scripts/meeting-resolver.py" meeting-id --join-url 'https://teams.microsoft.com/l/meetup-join/...')
"$SK/scripts/list-transcripts.sh" --meeting-id "$MID"
```

If that returns several transcripts, the link points at a recurring series. Show the dates and ask
which one, unless the user's message already named a date.

## 5. Download and convert

```bash
jq '.[0]' rows.json > row.json          # or select the row the user picked, by transcriptId
MEETING_ID=$(jq -r '.meetingId' row.json); TRANSCRIPT_ID=$(jq -r '.transcriptId' row.json)
DATE=$(jq -r '.eventStartLocal' row.json | cut -d' ' -f1)
SLUG=$(jq -r '.subject' row.json | tr '/\\:*?"<>|' '_________')   # only what a filesystem forbids
BASE="${DATE}_${SLUG}"                  # braces are required: $DATE_ would read as an empty variable

EM=$(jq -rn --arg s "$MEETING_ID" '$s|@uri'); ET=$(jq -rn --arg s "$TRANSCRIPT_ID" '$s|@uri')
m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/$EM/transcripts/$ET/content?\$format=text/vtt" \
  -o text > "$BASE.vtt"

# Metadata for the header, taken from the resolver row so the times carry an offset
jq --arg f "$BASE.vtt" '{subject, start: .eventStartUtc, end: .endedUtc, organizer,
   source: "Microsoft Graph", transcriptId, vttFile: $f}' row.json > meta.json

python3 "$SK/scripts/transcript-quality.py" --input "$BASE.vtt"   # exit 2 = poor, see section 8
python3 "$SK/scripts/transcript-to-text.py" --input "$BASE.vtt" --meta meta.json --output "$BASE.txt"
```

Take `start` and `end` from the resolver row, never by copying `start.dateTime` out of
`calendarView`: that string is naive, its zone depends on a header you did not send, and the
converter refuses it rather than print a time seven hours out.

**File names**: `YYYY-MM-DD_<subject>`, keeping Vietnamese diacritics intact. Replace only the
characters a filesystem forbids, `/ \ : * ? " < > |`. Write to the current directory unless the
user named another one.

**Then stop.** Print both paths and one line of what is in the `.txt` (meeting, time, how many
speakers and turns), then offer the next step:

> Saved. For minutes or a communication analysis, run the `meeting-minutes` skill on the `.txt`.

Do not summarize, do not quote highlights, do not call another skill. The user asked for a
transcript; spending their tokens on analysis they did not request is the failure mode here.

## 6. Adding attendance to the header

Only for meetings you organized, and only with `OnlineMeetingArtifact.Read.All`:

```bash
R=$(m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/$EM/attendanceReports" -o json --query 'value[0].id' | tr -d '"')
m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/$EM/attendanceReports/$R/attendanceRecords" \
  -o json --query 'value[].{name:identity.displayName, role:role, seconds:totalAttendanceInSeconds}'
```

Feed the result into `meta.json` as `attendees` (for example `"Trần Bảo Ngọc (54m)"`). The header
then shows who was invited, who actually came, and who spoke, which is exactly what a minutes
pass would otherwise have to ask for.

## 7. Channel meetings and recap links: the SharePoint route

A channel meeting keeps its recording and transcript in the team's SharePoint site, where the Graph
meeting routes do not look. The transcript hangs off the recording `.mp4` and is read through the
SharePoint host, `<site>/_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts`.
`scripts/sharepoint-transcript.py` does it in four subcommands: `parse` a `meetingrecap` link,
`find` the `.mp4` in a team site by file name, `list` its transcripts with `languageTag`, `download`
one. Full steps and the evidence: `references/sharepoint-route.md`.

Pitfalls, measured once on one channel meeting (one observation, not a tenant-wide rule):

| Pitfall                                     | Symptom                                         | Correct approach                                               |
| ------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------- |
| Same path on `graph.microsoft.com`          | **400**                                         | call the SharePoint host, `<site>/_api/v2.1/...`               |
| Calling `streamContent` on the transcript   | **406**                                         | use the `temporaryDownloadUrl` from the `media/transcripts` answer |
| `temporaryDownloadUrl` carries `tempauth`   | the link stops working after a short time       | list and fetch in one run (`download` does); never print or store the link |
| `languageTag` is not the meeting's language | a full-length VTT of plausible-looking nonsense | read `languageTag` first (`list` warns), then section 8        |

## 8. Wrong language or thin content

Teams transcribes in one spoken language, picked when transcription starts. A Vietnamese meeting
transcribed as `en-US` still yields a well-formed VTT of lines like "Ohh, chính, I think he would".
`scripts/transcript-quality.py` (already in section 5) catches it: it exits 2 with reasons when
few words carry Vietnamese letters or too few words per minute survived.

When it says `poor`, show the user the sample and the reasons, then **offer** to re-transcribe the
`.mp4` with `soniox stt transcribe --diarize --language-hints vi,en`. **Ask first, every time**:
this uploads meeting audio to an outside service. Soniox labels speakers `Speaker 1`, `Speaker 2`,
never by name; say so when handing the file over. Download, cleanup and the lasting fix (set the
spoken language to Vietnamese in Teams) are in `references/sharepoint-route.md` section 2.

---

## When there is no transcript

Work through the routes in order before saying so: Graph by organizer (section 1), Graph by
attendee (section 2), then SharePoint from the recording (section 7). Then name which case it is
rather than retrying:

- **Recording exists, transcript does not.** The meeting was recorded without live transcription.
  Offer the Soniox path in section 8, asking first. Downloading a recording you organized through
  Graph is in `references/advanced-commands.md`; for anything else use the `.mp4` in SharePoint.
- **The meeting is old enough that the `onlineMeeting` expired.** Per-meeting endpoints start
  failing; the bulk route or the SharePoint `.mp4` may still have it.
- **No recording and no transcript anywhere.** Nobody turned either on. Nothing to fetch.

## Known limits

Recordings of meetings other people organized through the Graph meeting routes (Microsoft blocks
this for delegated auth; the SharePoint `.mp4` may still be readable if the file is shared with
you). Assigning real names to `@1`, `@2` anonymous speakers or to Soniox's `Speaker n`: Teams
withholds guest names and Soniox never knew them, so the skill keeps the handle and says so rather
than guessing. Changing tenant configuration or app registrations: the preflight diagnoses and
hands you the wording, a human still has to act on it.

## Verified by running

Against a real tenant during this skill's build, on ordinary (non-channel) meetings only: paged
`getAllTranscripts` (9 transcripts across 2 pages), transcript download as VTT and as
`metadataContent`, the attended route (3 of 11 probed meetings organized by other people returned
transcripts, one returned `3003`, the rest were genuinely empty), decoding a `meetingId` and
matching it to a calendar event, correct occurrence selection for a weekly series,
`getAllRecordings` with delegated auth, and `attendanceRecords`.

Measured later, once, by the user on one channel meeting: the SharePoint `media/transcripts` call,
the 400 on Graph and 406 on `streamContent`, an `en-US` transcript of a Vietnamese meeting, and a
Soniox re-transcription of the `.mp4`. `sharepoint-transcript.py` was written from that session and
is covered by offline tests against a redacted recap link and a stubbed response; it has not yet
been run end-to-end against a tenant, and the exact field casing of the v2.1 answer is assumed.

Offline tests for every script are in `tests/`, run with `tests/run-tests.sh`.

Not exercised: a tenant with the policy switched off or mid-propagation (covered by tests against
a fake CLI), downloading recording content through Graph, and `sharepoint-transcript.py find`.

## References

| File                                          | When to read                                                                      |
| --------------------------------------------- | ----------------------------------------------------------------------------------- |
| `references/graph-recipes.md`                 | endpoint list, `meetingId` construction, paging loop, raw evidence for the pitfalls |
| `references/sharepoint-route.md`              | sections 7 and 8 in full: recap link, finding the `.mp4`, download, Soniox fallback, evidence |
| `references/advanced-commands.md`             | recordings and attendance in full                                                   |
| `../m365-calendar/SKILL.md`                   | anything about the calendar itself, including creating the meeting                  |
| `../m365-shared/references/authentication.md` | login methods and the two consent traps                                             |
| `../m365-sharepoint/SKILL.md`                 | resolving a team's site URL for section 7                                           |
