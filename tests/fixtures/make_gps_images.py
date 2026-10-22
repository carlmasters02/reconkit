"""Regenerate the GPS-tagged JPEG fixtures used by test_exif.py.

    python tests/fixtures/make_gps_images.py

Each image is an 8x8 white JPEG with Make/Model and a GPS IFD at a known
location, one per hemisphere combination the exif module has to sign.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent

# file name -> (lat, lon) in decimal degrees
GPS_IMAGES = {
    "gps_paris.jpg": (48.858370, 2.294481),     # N, E
    "gps_sydney.jpg": (-33.856784, 151.215297),  # S, E
    "gps_nyc.jpg": (40.689247, -74.044502),     # N, W
}
MAKE, MODEL = "TestMake", "TestModel"


def _dms(x: float) -> tuple[int, int, float]:
    x = abs(x)
    deg = int(x)
    minutes = int((x - deg) * 60)
    seconds = round(((x - deg) * 60 - minutes) * 60, 4)
    return deg, minutes, seconds


def main() -> None:
    for name, (lat, lon) in GPS_IMAGES.items():
        img = Image.new("RGB", (8, 8), "white")
        exif = img.getexif()
        exif[0x010F] = MAKE   # Make
        exif[0x0110] = MODEL  # Model
        exif[0x8825] = {      # GPSInfo IFD
            1: "N" if lat >= 0 else "S", 2: _dms(lat),
            3: "E" if lon >= 0 else "W", 4: _dms(lon),
        }
        img.save(HERE / name, exif=exif)
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
