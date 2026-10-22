"""exif: GPS extracted from committed fixture images must match the
coordinates they were written with (see fixtures/make_gps_images.py)."""

from __future__ import annotations

import pytest
from PIL import Image

from conftest import FIXTURES, assert_clean_failure, labels_values
from fixtures.make_gps_images import GPS_IMAGES, MAKE, MODEL


def read_back_gps(path) -> tuple[float, float]:
    """Decode the GPS IFD with Pillow's public API, independent of exif_mod."""
    g = Image.open(path).getexif().get_ifd(0x8825)

    def deg(dms, ref):
        d, m, s = (float(v) for v in dms)
        return (d + m / 60 + s / 3600) * (-1 if ref in ("S", "W") else 1)
    return deg(g[2], g[1]), deg(g[4], g[3])


@pytest.mark.parametrize("name", sorted(GPS_IMAGES))
def test_gps_and_maps_link(module, name):
    path = FIXTURES / name
    want_lat, want_lon = GPS_IMAGES[name]
    rb_lat, rb_lon = read_back_gps(path)

    r = module("exif").run(str(path))
    assert r.ok, r.error
    got = {f.label: f.value for f in r.findings}
    lat, lon = (float(x) for x in got["gps"].split(","))

    assert lat == pytest.approx(want_lat, abs=1e-5)
    assert lon == pytest.approx(want_lon, abs=1e-5)
    assert lat == pytest.approx(rb_lat, abs=1e-5)
    assert lon == pytest.approx(rb_lon, abs=1e-5)
    assert got["maps"] == f"https://maps.google.com/?q={lat},{lon}"
    assert got["Make"] == MAKE
    assert got["Model"] == MODEL


@pytest.mark.parametrize("suffix", [".jpg", ".png"])
def test_image_without_exif(module, tmp_path, suffix):
    path = tmp_path / f"plain{suffix}"
    Image.new("RGB", (8, 8)).save(path)
    r = module("exif").run(str(path))
    assert r.ok, r.error
    assert labels_values(r) == {("note", "no EXIF/GPS metadata present")}


def test_missing_path(module, tmp_path):
    assert_clean_failure(module("exif").run(str(tmp_path / "nope.jpg")), "file not found")


def test_directory(module, tmp_path):
    assert_clean_failure(module("exif").run(str(tmp_path)), "cannot read EXIF")


def test_not_an_image(module, tmp_path):
    path = tmp_path / "notimage.jpg"
    path.write_text("hello")
    assert_clean_failure(module("exif").run(str(path)), "cannot read EXIF")
