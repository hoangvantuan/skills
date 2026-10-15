# Recordings and attendance

Both are secondary to the transcript flow, and both only work for meetings **you organized**.
Read `../SKILL.md` first; the preflight, the two routes and the pitfalls all apply here too.

## Recordings

Listing works with delegated auth even though Microsoft documents this endpoint as
application-only, provided `meetingOrganizerUserId` is your own id:

```bash
ME=$(m365 request --url 'https://graph.microsoft.com/v1.0/me?$select=id' -o json --query 'id' | tr -d '"')
m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/getAllRecordings(meetingOrganizerUserId='$ME')" \
  -o json --query 'value[].{id:id, meetingId:meetingId, created:createdDateTime}'
```

This pages exactly like `getAllTranscripts`, with the same two traps: page one looks complete, and
the `nextLink` outlives the data. Page it the same way (`../scripts/list-transcripts.sh` is
transcript-specific; for recordings copy the loop from `graph-recipes.md` section 3).

Name the recordings by matching them to the calendar, the same way transcripts are matched:
`meeting-resolver.py match` takes any list of objects carrying `meetingId` and `createdDateTime`,
so recordings go through it unchanged.

### Downloading the content

```bash
m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/$ENC_MEETING/recordings/$ENC_REC/content" \
  -o text > recording.mp4
```

Only for meetings you organized. For anyone else's, Graph refuses with `userId must match
organizerId`, and that is a hard block for delegated auth, not something a scope fixes.

These are large files. Say the size and ask before downloading, and never fetch several at once
without the user asking for that.

**Finding the file in OneDrive instead**: recordings land in a folder whose name is *localized to
the owner's Teams language*. On a Vietnamese profile it is `Bản ghi`, not `Recordings`. Never
hardcode either. Search for the file, or take the URL Graph already gave you:

```bash
m365 request --url "https://graph.microsoft.com/v1.0/me/drive/root/search(q='.mp4')?\$select=name,webUrl,size" \
  -o json --query 'value[].{name:name, size:size}'
```

`m365-onedrive` covers the file operations once you have located it.

### No transcript, only a recording

This is common: the meeting was recorded but live transcription was never switched on. Download
the recording and hand it to the `speech-to-text` skill, which transcribes audio through Soniox.
Say that plainly rather than reporting "no transcript" as a dead end.

## Attendance

Needs `OnlineMeetingArtifact.Read.All`. One meeting can have several reports, one per session:

```bash
ENC=$(jq -rn --arg s "$MEETING_ID" '$s|@uri')
m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/$ENC/attendanceReports" \
  -o json --query 'value[].{id:id, start:meetingStartDateTime, people:totalParticipantCount}'

REPORT_ID="..."   # usually value[0] for a single-session meeting
m365 request --url "https://graph.microsoft.com/v1.0/users/$ME/onlineMeetings/$ENC/attendanceReports/$REPORT_ID/attendanceRecords" \
  -o json --query 'value[].{name:identity.displayName, role:role, seconds:totalAttendanceInSeconds, email:emailAddress}'
```

`$expand=attendanceRecords` on the reports collection returns the report with an empty records
field. It looks like "nobody attended" rather than an error, so use the sub-endpoint.

Measured shape:

| Field                      | Example                 | Note                                                   |
| -------------------------- | ----------------------- | -------------------------------------------------------- |
| `identity.displayName`     | `Trần Bảo Ngọc`        | the tenant display name, not the transcript speaker tag |
| `role`                     | `Presenter`, `Attendee` | Teams role during the meeting                          |
| `totalAttendanceInSeconds` | `3248`                  | summed across joins and rejoins                        |

### Feeding it into the transcript header

Attendance answers a question the transcript cannot: who was there and said nothing. Convert to
minutes and pass as `attendees` in the converter's metadata file:

```bash
jq '[.[] | "\(.name) (\((.seconds / 60) | floor)m)"]' attendance.json
```

The `.txt` header then carries invited, present, and speaking as three separate lists, which is
what a minutes or participation analysis needs and would otherwise have to ask for.

Names here will not always line up with the transcript's speaker labels: a guest from outside the
tenant shows a real display name in attendance but `@1` in the transcript. Leave both as they are.
Reconciling them is guesswork, and it is explicitly out of scope.

## Known blocks

| Wanted                             | Result                                                        |
| ---------------------------------- | --------------------------------------------------------------- |
| Recording of someone else's meeting | `userId must match organizerId`, hard block for delegated auth |
| Attendance for someone else's meeting | 403, same reason                                             |
| Channel meeting artifacts           | not returned by these routes; read the recording's transcript from SharePoint, `sharepoint-route.md` |
| Expired `onlineMeeting`             | per-meeting endpoints fail; the bulk list may still hold the item |
