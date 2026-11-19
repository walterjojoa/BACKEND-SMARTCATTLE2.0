"""What counts as a place a camera can be reached at.

Until this existed the field took any text at all: "abc" was saved and answered
201, and the camera simply never came online. The person who typed it got no
hint that the problem was the value they entered, so this names the problem
when it is still on screen.

The message is the one the person reads, so it is in Spanish, like the rest of
what the API says to them.
"""

import ipaddress
import re
from urllib.parse import urlsplit

#: Imou serial numbers as the app and the label on the device show them: letters
#: and digits, no separators. Theirs run to 15, with older ones a little shorter.
IMOU_SERIAL = re.compile(r"^[0-9A-Z]{9,20}$")

#: A webcam plugged into the machine running the AI service, addressed by index.
#: OpenCV takes the number straight, and 0 is the usual one.
WEBCAM_INDEX = re.compile(r"^\d{1,2}$")

SCHEMES = ("rtsp", "http", "https")

#: A phone or PC broadcasting from the dashboard page itself. It has no address:
#: its browser sends the pictures to the AI service, and this word is what the
#: frontend saves for it (DEVICE_SOURCE). Refusing it made "Transmitir" fail with a 400.
DEVICE_SOURCE = "browser"

PROBLEM = (
    "Escribe la dirección de la cámara: una IP como 192.168.1.50 (con puerto si lo usa), "
    "un enlace rtsp:// o http:// , el número de serie Imou, o el número de una cámara web (0)."
)


def _is_ipv4(value: str) -> bool:
    """An IPv4 address, with an optional :port and an optional path.

    The path matters: scanning the network offers DroidCam phones as
    "192.168.1.20:4747/video", and that is the value saved for them.
    """
    authority, _, _path = value.partition("/")
    host, _, port = authority.rpartition(":")
    if host and port.isdigit():
        if not 1 <= int(port) <= 65535:
            return False
        authority = host
    elif host:
        # A colon with something other than a port after it.
        return False
    try:
        ipaddress.IPv4Address(authority)
    except ValueError:
        return False
    return True


def _is_url(value: str) -> bool:
    parts = urlsplit(value)
    # A netloc is what separates "rtsp://192.168.1.50/live" from the bare word
    # "rtsp:" that urlsplit also parses happily.
    return parts.scheme in SCHEMES and bool(parts.hostname)


def describe_source_problem(source: str) -> str | None:
    """The reason this is not somewhere a camera can be reached, or None when it is.

    Returning the message rather than raising lets the caller decide the status
    code: the route answers 400, and the schema keeps its own rules separate.
    """
    value = source.strip()
    if not value:
        return PROBLEM
    if value == DEVICE_SOURCE:
        return None
    if _is_url(value) or _is_ipv4(value) or WEBCAM_INDEX.match(value) or IMOU_SERIAL.match(value):
        return None
    return PROBLEM
