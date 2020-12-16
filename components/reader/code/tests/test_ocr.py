# -*- coding: utf-8 -*-

import os
import pytest
from ocr_wrapper import alpr as ocr_reader


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_files",
)

testdata_ocr_files = [
    [os.path.join(FIXTURE_DIR, "plate1.jpg"), "FPZ396"],
]


@pytest.mark.parametrize("filename,expected", testdata_ocr_files)
def test_ocr(filename, expected):
    plates = ocr_reader.read_file(filename)

    assert plates
    assert plates["results"][0]["plate"].upper() == expected.upper()
