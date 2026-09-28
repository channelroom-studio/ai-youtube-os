"""Self-checks: python3 test_scripts.py"""
from preflight import checks, last_caption_end
from render import plan_durations


def info(w, h, dur, audio=True):
    streams = [{"codec_type": "video", "width": w, "height": h}]
    if audio:
        streams.append({"codec_type": "audio"})
    return {"streams": streams, "format": {"duration": str(dur)}}


def statuses(rows):
    return {name: status for status, name, _ in rows if name != "duration" or status != "PASS"}


def test_should_stretch_last_scene_when_audio_is_longer():
    assert plan_durations([2.0, 3.0], 7.5) == [2.0, 5.5]


def test_should_keep_durations_when_video_covers_audio():
    assert plan_durations([4.0, 4.0], 6.0) == [4.0, 4.0]


def test_should_reject_empty_or_nonpositive_scenes():
    for bad in ([], [1.0, 0.0]):
        try:
            plan_durations(bad, 5.0)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad}")


def test_should_fail_when_audio_track_missing():
    assert statuses(checks(info(1080, 1920, 30, audio=False), None, None, None))["audio"] == "FAIL"


def test_should_fail_when_audio_is_silent():
    assert statuses(checks(info(1080, 1920, 30), -91.0, -91.0, None))["audio"] == "FAIL"


def test_should_warn_when_shorts_too_long():
    rows = checks(info(1080, 1920, 200), -20.0, -3.0, None)
    assert ("WARN", "duration") in {(s, n) for s, n, _ in rows}


def test_should_warn_when_captions_end_early():
    assert statuses(checks(info(1080, 1920, 50), -20.0, -3.0, 30.0))["captions"] == "WARN"


def test_should_parse_last_srt_cue():
    srt = "1\n00:00:00,000 --> 00:00:02,500\nhi\n\n2\n00:00:03,000 --> 00:00:52,250\nbye\n"
    assert last_caption_end(srt) == 52.25


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"{len(tests)} passed")
