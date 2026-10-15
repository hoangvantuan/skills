#!/usr/bin/env python3
"""Behaviour of the resolver: transcripts plus calendar events in, named meetings out."""
import importlib.util
import json
import pathlib
import unittest

HERE = pathlib.Path(__file__).parent
FIX = HERE / "fixtures"
spec = importlib.util.spec_from_file_location("res", HERE.parent / "scripts" / "meeting-resolver.py")
res = importlib.util.module_from_spec(spec)
spec.loader.exec_module(res)

A_OID, A_TH = "11111111-1111-1111-1111-111111111111", "19:meeting_AAAAweekly@thread.v2"
load = lambda n: json.loads((FIX / n).read_text(encoding="utf-8"))["value"]


class MeetingId(unittest.TestCase):
    def test_round_trips_between_the_id_and_its_parts(self):
        self.assertEqual(res.decode_meeting_id(res.build_meeting_id(A_OID, A_TH)), (A_OID, A_TH))

    def test_decodes_an_id_with_the_shape_measured_on_a_real_tenant(self):
        oid, thread = res.decode_meeting_id(
            "MSo1NTU1NTU1NS01NTU1LTU1NTUtNTU1NS01NTU1NTU1NTU1NTUqMCoqMTk6bWVldGluZ19OelV3WVdVME1qWXRNMlJpTmkwMFlUVXdMV0ZqWkRRdFlUa3dPVGhtWkROaFkyWmpAdGhyZWFkLnYy")
        self.assertEqual(oid, "55555555-5555-5555-5555-555555555555")
        self.assertTrue(thread.startswith("19:meeting_") and thread.endswith("@thread.v2"))

    def test_rejects_an_id_that_is_not_shaped_like_a_meeting_id(self):
        import base64
        with self.assertRaises(ValueError):
            res.decode_meeting_id(base64.b64encode(b"not-a-meeting").decode())

    def test_reads_thread_and_organizer_out_of_an_encoded_join_url(self):
        url = ("https://teams.microsoft.com/l/meetup-join/19%3Ameeting_AAAAweekly%40thread.v2/0"
               "?context=%7B%22Tid%22%3A%22t%22%2C%22Oid%22%3A%2211111111-1111-1111-1111-111111111111%22%7D")
        self.assertEqual(res.parse_join_url(url), (A_OID, A_TH))

    def test_builds_the_id_an_attended_meeting_needs_straight_from_its_join_url(self):
        url = [e["onlineMeeting"]["joinUrl"] for e in load("events.json")
               if e.get("onlineMeeting") and "AAAAweekly" in e["onlineMeeting"]["joinUrl"]][0]
        self.assertEqual(res.build_meeting_id(*res.parse_join_url(url)), res.build_meeting_id(A_OID, A_TH))


class Match(unittest.TestCase):
    def setUp(self):
        self.rows = res.match(load("transcripts.json"), load("events.json"))
        self.by_id = {r["transcriptId"]: r for r in self.rows}

    def test_a_recurring_series_resolves_to_the_right_occurrence(self):
        # Five Tuesdays share one thread id, so only the start time can tell them apart.
        self.assertEqual(self.by_id["transcript-1"]["eventStartLocal"], "2026-09-15 10:00")
        self.assertEqual(self.by_id["transcript-2"]["eventStartLocal"], "2026-09-08 10:00")
        for t in ("transcript-1", "transcript-2"):
            self.assertEqual(self.by_id[t]["subject"], "[Solution] Weekly MTG")

    def test_a_meeting_spanning_utc_midnight_is_not_pushed_onto_the_wrong_day(self):
        # 06:00 on 11 Sep in GMT+7 is 23:00 on 10 Sep in UTC. Comparing dates as text would miss it.
        row = self.by_id["transcript-3"]
        self.assertTrue(row["matched"])
        self.assertEqual(row["subject"], "Chặng 3 meeting")
        self.assertEqual(row["eventStartLocal"], "2026-09-11 06:00")

    def test_a_transcript_with_no_event_is_reported_unmatched_not_guessed(self):
        row = self.by_id["transcript-4"]
        self.assertFalse(row["matched"])
        self.assertIsNone(row["subject"])
        self.assertNotIn("gapMinutes", row)

    def test_tolerance_rejects_a_pairing_that_is_merely_the_nearest(self):
        tight = {r["transcriptId"]: r for r in res.match(load("transcripts.json"), load("events.json"),
                                                         tolerance_min=2)}
        self.assertFalse(tight["transcript-1"]["matched"])
        self.assertEqual(tight["transcript-1"]["gapMinutes"], 5.0)  # still reported, just not trusted

    def test_the_window_filters_on_instants_not_on_calendar_days(self):
        rows = res.match(load("transcripts.json"), load("events.json"),
                         start=res._utc("2026-09-10T17:00:00Z", "UTC"),
                         end=res._utc("2026-09-14T17:00:00Z", "UTC"))
        self.assertEqual({r["transcriptId"] for r in rows}, {"transcript-3", "transcript-4"})

    def test_newest_first_so_the_common_ask_sits_at_the_top(self):
        self.assertEqual([r["transcriptId"] for r in self.rows],
                         ["transcript-1", "transcript-4", "transcript-3", "transcript-2"])

    def test_an_event_without_an_online_meeting_is_skipped_rather_than_fatal(self):
        self.assertTrue(any(e.get("onlineMeeting") is None for e in load("events.json")))
        self.assertEqual(len(self.rows), 4)

    def test_a_channel_meeting_is_flagged_so_the_silence_can_be_explained(self):
        idx = res.index_events(load("events.json"))
        channel = [v for k, v in idx.items() if "tacv2" in k]
        self.assertTrue(channel and channel[0][0]["isChannel"])


class Attended(unittest.TestCase):
    def test_lists_only_threads_someone_else_organized(self):
        rows = res.attended(load("events.json"), A_OID)
        self.assertEqual([r["subject"] for r in rows], ["Chặng 3 meeting"])

    def test_one_row_per_thread_so_a_series_costs_one_graph_call(self):
        rows = res.attended(load("events.json"), "99999999-9999-9999-9999-999999999999")
        weekly = [r for r in rows if r["subject"] == "[Solution] Weekly MTG"]
        self.assertEqual(len(weekly), 1)
        self.assertEqual(weekly[0]["occurrences"], 5)

    def test_each_row_carries_the_meeting_id_the_transcripts_endpoint_wants(self):
        row = res.attended(load("events.json"), A_OID)[0]
        self.assertEqual(res.decode_meeting_id(row["meetingId"])[1], row["threadId"])

    def test_channel_meetings_are_left_out_by_default_because_this_route_never_returns_them(self):
        rows = res.attended(load("events.json"), "99999999-9999-9999-9999-999999999999")
        self.assertFalse(any("tacv2" in r["threadId"] for r in rows))

    def test_include_channel_surfaces_them_flagged_for_the_sharepoint_route(self):
        rows = res.attended(load("events.json"), "99999999-9999-9999-9999-999999999999", include_channel=True)
        channel = [r for r in rows if "tacv2" in r["threadId"]]
        self.assertEqual(len(channel), 1)
        self.assertTrue(channel[0]["isChannel"])


class Handoff(unittest.TestCase):
    """The converter refuses a naive timestamp, so match() has to emit an unambiguous one."""

    def test_the_matched_start_carries_an_offset_the_converter_will_accept(self):
        import importlib.util
        rows = res.match(load("transcripts.json"), load("events.json"))
        start = [r for r in rows if r["matched"]][0]["eventStartUtc"]
        self.assertIn("+00:00", start)
        spec2 = importlib.util.spec_from_file_location(
            "conv2", HERE.parent / "scripts" / "transcript-to-text.py")
        conv = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(conv)
        self.assertEqual(conv.local(start), "2026-09-15 10:00")

    def test_rows_say_which_route_found_them(self):
        rows = res.match(load("transcripts.json"), load("events.json"), me=A_OID)
        self.assertEqual({r["role"] for r in rows}, {"organizer", "attendee"})


class Timezones(unittest.TestCase):
    def test_accepts_the_utc_that_a_prefer_free_calendarview_returns(self):
        self.assertEqual(res._utc("2026-09-15T03:00:00.0000000", "UTC").hour, 3)

    def test_converts_the_local_time_a_prefer_header_would_have_produced(self):
        self.assertEqual(res._utc("2026-09-15T10:00:00.0000000", "SE Asia Standard Time").hour, 3)

    def test_refuses_a_zone_it_cannot_convert_instead_of_guessing(self):
        # Guessing here is a silent seven-hour error that picks a neighbouring occurrence.
        with self.assertRaises(SystemExit) as cm:
            res._utc("2026-09-15T10:00:00", "Tokyo Standard Time")
        self.assertIn("Prefer", str(cm.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
