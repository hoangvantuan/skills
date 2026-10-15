#!/usr/bin/env python3
"""The SharePoint route for channel meetings, and the check that catches a wrong-language transcript.

The recap link fixture is shaped after Teams' meetingrecap links with every id redacted; no
network is touched, m365 and the tempauth download are both stubbed.
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).parent
FIX = HERE / "fixtures"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE.parent / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sp = load_script("sharepoint-transcript")
q = load_script("transcript-quality")
RECAP = (FIX / "recap-link.txt").read_text().strip()


class RecapLink(unittest.TestCase):
    def test_pulls_the_drive_and_item_ids_out_of_a_recap_link(self):
        r = sp.parse_recap(RECAP)
        self.assertEqual(r["driveId"], "b!AAAAdriveAAAA_redacted")
        self.assertEqual(r["driveItemId"], "01ITEMREDACTED")

    def test_derives_the_site_the_v21_route_must_be_called_on(self):
        self.assertEqual(sp.parse_recap(RECAP)["siteUrl"], "https://contoso.sharepoint.com/sites/SolutionTeam")

    def test_decodes_the_doubly_encoded_vietnamese_folder_name(self):
        self.assertIn("/Bản ghi/", sp.parse_recap(RECAP)["fileUrl"])

    def test_flags_a_channel_meeting(self):
        self.assertTrue(sp.parse_recap(RECAP)["isChannel"])

    def test_a_join_link_is_refused_with_a_reason(self):
        with self.assertRaises(ValueError):
            sp.parse_recap("https://teams.microsoft.com/l/meetup-join/19%3ameeting_x%40thread.v2/0")

    def test_site_url_handles_teams_and_personal_roots(self):
        self.assertEqual(sp.site_url("https://t.sharepoint.com/teams/X/Docs/a.mp4"), "https://t.sharepoint.com/teams/X")
        self.assertEqual(sp.site_url("https://t-my.sharepoint.com/personal/u_t_com/Documents/a.mp4"),
                         "https://t-my.sharepoint.com/personal/u_t_com")


class SharePointTranscripts(unittest.TestCase):
    def run_main(self, *argv):
        payload = json.loads((FIX / "sp-transcripts.json").read_text())
        fake = io.BytesIO(b"WEBVTT\n")
        fake.__enter__ = lambda s=fake: s
        fake.__exit__ = lambda *a: False
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sp, "m365_json", return_value=payload) as call, \
                mock.patch.object(sp.urllib.request, "urlopen", return_value=fake), \
                mock.patch("sys.argv", ["x", *argv]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            sp.main()
        return call, out.getvalue(), err.getvalue()

    def test_calls_the_sharepoint_host_not_graph(self):
        call, _, _ = self.run_main("list", "--recap-url", RECAP)
        url = call.call_args[0][0]
        self.assertTrue(url.startswith("https://contoso.sharepoint.com/sites/SolutionTeam/_api/v2.1/drives/"))
        self.assertTrue(url.endswith("/items/01ITEMREDACTED/media/transcripts"))

    def test_warns_when_the_transcript_language_is_not_the_meetings(self):
        _, out, err = self.run_main("list", "--recap-url", RECAP)
        self.assertIn("en-US", err)
        self.assertIn("WARNING", err)

    def test_never_prints_the_tempauth_link(self):
        _, out, _ = self.run_main("list", "--recap-url", RECAP)
        self.assertNotIn("tempauth", out)

    def test_download_writes_the_vtt_in_the_same_run(self):
        with tempfile.TemporaryDirectory() as d:
            dest = pathlib.Path(d) / "m.vtt"
            _, out, _ = self.run_main("download", "--recap-url", RECAP, "--output", str(dest))
            self.assertEqual(dest.read_text(), "WEBVTT\n")
            self.assertNotIn("tempauth", out)

    def test_language_match_ignores_region_and_case(self):
        self.assertTrue(sp.lang_matches("vi-vn", "vi-VN"))
        self.assertFalse(sp.lang_matches("en-US", "vi-VN"))


class Quality(unittest.TestCase):
    def test_a_vietnamese_meeting_transcribed_as_english_is_poor(self):
        lines, minutes = q.read_text(FIX / "wrong-language.vtt")
        r = q.assess(lines, minutes, "vi", 0.35, 40)
        self.assertEqual(r["verdict"], "poor")
        self.assertLess(r["vietnameseWordRatio"], 0.35)
        self.assertEqual(r["minutes"], 25.0)

    def test_a_real_vietnamese_transcript_passes_the_language_check(self):
        lines, _ = q.read_text(FIX / "sample.vtt")
        r = q.assess(lines, None, "vi", 0.35, 40)
        self.assertEqual(r["verdict"], "ok")
        self.assertGreater(r["vietnameseWordRatio"], 0.5)

    def test_too_few_words_for_the_length_is_poor_even_in_vietnamese(self):
        lines, _ = q.read_text(FIX / "sample.vtt")
        self.assertIn("words/minute", " ".join(q.assess(lines, 25, "vi", 0.35, 40)["reasons"]))

    def test_reads_the_spoken_text_out_of_metadata_content(self):
        lines, _ = q.read_text(FIX / "sample-metadata.vtt")
        self.assertTrue(lines and not any(line.startswith("{") for line in lines))

    def test_an_english_meeting_is_not_judged_on_vietnamese_letters(self):
        lines, minutes = q.read_text(FIX / "wrong-language.vtt")
        self.assertEqual(q.assess(lines, minutes, "en", 0.35, 0)["verdict"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
