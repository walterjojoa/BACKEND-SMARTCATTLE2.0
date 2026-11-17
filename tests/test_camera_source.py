import pytest

from app.core.camera_source import PROBLEM, describe_source_problem


@pytest.mark.parametrize("source", [
    "192.168.1.50",
    "192.168.1.50:554",
    "10.0.0.8:8080",
    # What scanning the network offers for a DroidCam phone, and what gets saved for it.
    "192.168.1.20:4747/video",
    "192.168.1.20:8080/video",
    "rtsp://192.168.1.50/live",
    "rtsp://192.168.1.50:554/cam/realmonitor",
    "http://192.168.1.50:8080/video",
    "https://camara.finca.example/stream",
    # The AI service reaches a webcam plugged into its own machine by index.
    "0",
    "1",
    # An Imou serial, as the label on the device prints it.
    "7J0A12ABCDEF345",
])
def test_a_reachable_camera_is_accepted(source):
    assert describe_source_problem(source) is None


@pytest.mark.parametrize("source", [
    "abc",
    "mi camara",
    "",
    "   ",
    # Looks like an address until you read it: no scheme that opens a stream.
    "ftp://192.168.1.50/live",
    "rtsp://",
    # Out of range by one, in each direction.
    "999.1.1.1",
    "192.168.1.50:0",
    "192.168.1.50:70000",
    "192.168.1.50:abc",
])
def test_anything_a_camera_cannot_be_reached_at_is_refused(source):
    assert describe_source_problem(source) == PROBLEM


def test_the_message_tells_the_person_what_to_type():
    """The point of the message is the examples, not the word "inválido"."""
    problem = describe_source_problem("abc")
    assert problem is not None
    for example in ("192.168.1.50", "rtsp://", "Imou"):
        assert example in problem


def test_surrounding_spaces_do_not_decide_the_answer():
    assert describe_source_problem("  192.168.1.50  ") is None
