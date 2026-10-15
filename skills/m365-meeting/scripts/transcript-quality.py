#!/usr/bin/env python3
"""Is this transcript worth reading? A cheap check before anyone builds minutes on it.

Teams transcribes in ONE spoken language, chosen when transcription starts. Set to en-US on a
Vietnamese meeting it still produces a full-length, well-formed VTT, just full of lines like
"Ohh, chính, I think he would". Nothing in the file's shape says it is garbage, so look at the
words: how many carry Vietnamese letters, and how many words per minute survived.

Prints a JSON verdict and exits 0 when the transcript looks usable, 2 when it does not.
The thresholds are starting estimates, not measurements over many meetings; adjust with flags.

  transcript-quality.py --input meeting.vtt [--expect vi] [--minutes 25]
"""
import argparse
import json
import re
import sys

TIMING = re.compile(r"(\d+:)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d+:)?(\d{2}):(\d{2})[.,](\d{3})")
VOICE = re.compile(r"</?v[^>]*>|<[^>]+>")
# Letters that exist in Vietnamese and not in English: đ, the hats and horns, and every tone mark.
VI_CHARS = set("đăâêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ")
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _seconds(h, m, s, ms):
    return int((h or "0:")[:-1] or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def read_text(path):
    """Spoken text only, from a VTT, a metadataContent VTT, or a plain .txt with speaker labels."""
    lines, last_end = [], 0.0
    with open(path, encoding="utf-8-sig") as fh:
        raw_lines = fh.read().splitlines()
    for raw in raw_lines:
        line = raw.strip()
        t = TIMING.search(line)
        if t:
            last_end = max(last_end, _seconds(*t.groups()[4:]))
            continue
        if not line or line == "WEBVTT" or line.startswith("NOTE") or line.isdigit():
            continue
        if line.startswith("{"):
            try:
                line = json.loads(line).get("spokenText") or ""
            except ValueError:
                pass
        lines.append(VOICE.sub("", line).strip())
    return [x for x in lines if x], last_end / 60


def assess(lines, minutes, expect, min_vi_ratio, min_wpm):
    words = [w.lower() for line in lines for w in WORD.findall(line)]
    vi_words = sum(1 for w in words if VI_CHARS & set(w))
    ratio = vi_words / len(words) if words else 0.0
    wpm = len(words) / minutes if minutes else None
    reasons = []
    if not words:
        reasons.append("no spoken text at all")
    if expect == "vi" and words and ratio < min_vi_ratio:
        reasons.append(f"only {ratio:.0%} of words carry Vietnamese letters (expected >= {min_vi_ratio:.0%}): "
                       "the transcript was probably recognised in the wrong language")
    if wpm is not None and words and wpm < min_wpm:
        reasons.append(f"{wpm:.0f} words/minute over {minutes:.0f} minutes (expected >= {min_wpm}): "
                       "most of the speech is missing")
    return {
        "verdict": "poor" if reasons else "ok", "reasons": reasons,
        "words": len(words), "minutes": round(minutes, 1) if minutes else None,
        "wordsPerMinute": round(wpm) if wpm is not None else None,
        "vietnameseWordRatio": round(ratio, 2), "sample": lines[:5],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help=".vtt, metadataContent .vtt, or .txt")
    ap.add_argument("--expect", default="vi", help="language the meeting was held in, default vi")
    ap.add_argument("--minutes", type=float, help="meeting length; default: the last cue's end time")
    ap.add_argument("--min-vi-ratio", type=float, default=0.35)
    ap.add_argument("--min-wpm", type=float, default=40)
    args = ap.parse_args()

    lines, cue_minutes = read_text(args.input)
    report = assess(lines, args.minutes or cue_minutes, args.expect.lower().split("-")[0],
                    args.min_vi_ratio, args.min_wpm)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(2 if report["verdict"] == "poor" else 0)


if __name__ == "__main__":
    main()
