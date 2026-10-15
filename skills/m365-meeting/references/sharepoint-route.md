# The SharePoint route and the Soniox fallback

Read `../SKILL.md` first: the order of routes, the file naming and the "then stop" rule all apply.
`$SK` is the skill directory, as there.

## Contents

1. Reading the transcript from the recording
2. Wrong language or thin content: check, then offer to re-transcribe
3. Raw evidence

---

## 1. Reading the transcript from the recording

A channel meeting keeps its recording and its transcript in the team's SharePoint site, not where
the Graph meeting routes look. The transcript hangs off the recording `.mp4` and can be read
through the SharePoint host's v2.1 API:

```
GET https://<tenant>.sharepoint.com/sites/<site>/_api/v2.1/drives/{driveId}/items/{itemId}/media/transcripts
```

`scripts/sharepoint-transcript.py` wraps it. Three ways in, cheapest first:

```bash
SP="$SK/scripts/sharepoint-transcript.py"

# a) the user pasted a meetingrecap link: it already names the recording
python3 "$SP" parse --recap-url "$RECAP" > recap.json   # driveId, driveItemId, siteUrl, fileUrl, isChannel; no network
DRIVE=$(jq -r .driveId recap.json); ITEM=$(jq -r .driveItemId recap.json); SITE=$(jq -r .siteUrl recap.json)
python3 "$SP" list  --recap-url "$RECAP"                 # transcripts + languageTag, read this BEFORE downloading

# b) only a channel meeting (join URL or calendar event): find the .mp4 in the team's site.
#    Site URL from the team's group, non-admin: see ../m365-sharepoint/SKILL.md "Resolve Team/Group Site URL"
SITE="https://<tenant>.sharepoint.com/sites/<site>"
python3 "$SP" find --site-url "$SITE" > recordings.json    # newest first; pick the row, then:
DRIVE=$(jq -r '.[0].driveId' recordings.json); ITEM=$(jq -r '.[0].driveItemId' recordings.json)
python3 "$SP" list --site-url "$SITE" --drive-id "$DRIVE" --item-id "$ITEM"

# c) name the files from the recording, same rule as ../SKILL.md section 5: YYYY-MM-DD_<subject>.
#    "Họp tuần-20261010_090312-Meeting Recording.mp4" -> BASE="2026-10-10_Họp tuần"
#    then download one; it is fetched in the same run because the link expires
python3 "$SP" download --site-url "$SITE" --drive-id "$DRIVE" --item-id "$ITEM" \
  --output "$BASE.vtt" [--transcript-id <id>]
```

`find` searches by file name (`... Meeting Recording.mp4`), never by folder: the recordings folder
is named after the team's language, `Recordings` in one team and `Bản ghi` in another. Pick the
file whose name carries the meeting's date and time (`..._YYYYMMDD_HHMMSS-Meeting Recording.mp4`)
and confirm it with the user if more than one fits. A file uploaded minutes ago may not be in the
search index yet.

`list` prints a `WARNING` on stderr for any transcript whose `languageTag` is not the meeting's
language (default `vi-VN`, change with `--expect-lang`). Show it to the user before downloading;
see section 2 for what to do about it.

After download, continue with `../SKILL.md` section 5 from the quality check on. There is no resolver row, so
write `meta.json` by hand: `subject` from the recording's name, `start` from the transcript's
`createdDateTime` (it carries `Z`), `source: "SharePoint media/transcripts"`. Leave out anything you
do not know rather than guess it.

The pitfalls of this route are tabled in `../SKILL.md` section 7; the evidence is section 3 below.

## 2. Wrong language or thin content: check, then offer to re-transcribe

Teams transcribes in one spoken language, picked when transcription starts. A Vietnamese meeting
transcribed as `en-US` still yields a well-formed VTT, full of lines like "Ohh, chính, I think he
would", and the file is thin for its length (21 KB for 25 minutes in the case that prompted this
check). Nothing in the file's shape gives it away, so check the words:

```bash
python3 "$SK/scripts/transcript-quality.py" --input "$BASE.vtt" [--expect vi] [--minutes 25]
```

It prints the first lines, the share of words carrying Vietnamese letters, and words per minute,
and exits 2 with reasons when the transcript looks unusable. Defaults (35%, 40 words/minute) are
starting estimates; change them with `--min-vi-ratio` and `--min-wpm`. On the Graph routes there
is no `languageTag` to read in advance; `metadataContent` carries `spokenLanguage` per cue if you
need the same signal before converting.

When it says `poor`, show the user the sample and the reasons, then **offer** to re-transcribe the
recording with Soniox. Ask first, every time: this uploads the meeting audio to an outside service,
and that is the user's call, not the skill's.

```bash
# the .mp4: Graph serves the drive item a SharePoint transcript hangs off
m365 request --url "https://graph.microsoft.com/v1.0/drives/$DRIVE/items/$ITEM" -o json > item.json
curl -sS -o "$BASE.mp4" "$(jq -r '."@microsoft.graph.downloadUrl"' item.json)"   # short-lived link too

soniox stt transcribe "$BASE.mp4" --diarize --language-hints vi,en --timestamps -o "$BASE.soniox.txt"
```

The `soniox` CLI extracts the audio itself (a 213 MB `.mp4` became about 10 MB of audio and took a
few minutes) and deletes both its temporary audio file and the job on Soniox when it finishes.
The `.mp4` you downloaded is yours to remove once the transcript is saved, unless the user wants
to keep it. The in-repo `speech-to-text` skill is the alternative when the CLI is not installed.

Soniox labels speakers `Speaker 1`, `Speaker 2`, never by name. Say so when handing the file over:
whoever builds minutes from it cannot assign owners by name.

Outside this skill, the lasting fix is to set the spoken language to Vietnamese when starting
transcription in Teams. Mention it once when a wrong-language transcript was the cause.

## 3. Raw evidence

Observed once, by the user, on one channel meeting after the rest of this file was measured. It
is recorded here as that single observation.

**Where the ids come from.** A Teams recap link looks like this (ids redacted, same shape as
`tests/fixtures/recap-link.txt`):

```
https://teams.microsoft.com/l/meetingrecap?driveId=b%21...&driveItemId=01...&sitePath=https%3A%2F%2F<tenant>.sharepoint.com%2Fsites%2F<site>%2FShared%2520Documents%2F<channel>%2FB%25E1%25BA%25A3n%2520ghi%2F...-Meeting%2520Recording.mp4&threadId=19%3A...%40thread.tacv2&...
```

`sitePath` is encoded twice (`%2520` is a space). The site to call is its first two path segments,
`/sites/<site>` or `/teams/<site>`. Without a recap link, Graph search on the site's drive for
`Meeting Recording` returns the `.mp4` with `id` and `parentReference.driveId`; those are the same
ids the v2.1 route takes.

**What answered and what did not.**

| Call                                                                 | Result |
| -------------------------------------------------------------------- | ------ |
| `graph.microsoft.com/v1.0/drives/{d}/items/{i}/media/transcripts`    | 400    |
| `<site>/_api/v2.1/drives/{d}/items/{i}/media/transcripts`            | 200, one transcript with `languageTag` and `temporaryDownloadUrl` |
| `.../media/transcripts/{id}/streamContent` called directly           | 406    |
| `temporaryDownloadUrl` via plain `curl`, no auth header              | 200, a WEBVTT file |

`m365 request` acquires a token for whichever host the URL names, so the SharePoint call needs no
extra login. The download link carries `tempauth` and expires; fetch it in the same run.

**The language trap.** The transcript came back `en-US` for a meeting held in Vietnamese. The VTT
was well-formed, 21 KB for 25 minutes, and read like "Ohh, chính, I think he would". Re-running the
213 MB `.mp4` through `soniox stt transcribe --language-hints vi,en` took a few minutes and gave a
usable transcript with `Speaker 1/2` labels.
