# -*- coding: utf-8 -*-
import pytest
from utils import get_alt_representation
from utils import get_valid_plates
from utils import rm_duplicates_1edit_away

testdata_alt_rep = [
    ["ABC123", "ABC123"],
    ["ABC12", "ABC12"],
    ["BCI2", "BCI2"],
    ["AC023I", "ACO231"],
    ["C00III", "COO111"],
    ["CDEI11", "CDE111"],
]

testdata_valid_plates = [
    ["ABC123", ["ABC123", "ABC12", "BC123", "ABC1", "BC12", "BC1"]],
    ["AABC123", ["ABC123", "ABC12", "BC123", "ABC1", "BC12", "BC1"]],
    ["ABC1234", ["ABC123", "ABC12", "BC123", "ABC1", "BC12", "BC1"]],
    ["AABC123A", ["ABC123", "ABC12", "BC123", "ABC1", "BC12", "BC1"]],
    ["HX345", ["HX345", "HX34", "HX3"]],
    ["ZF85", ["ZF85", "ZF8"]],
    ["A023", ["AO23", "AO2"]],
    ["YB7", ["YB7"]],
    ["ABC012", []],
    ["DA123", []],
    ["PA123", []],
    ["WA123", []],
    ["ÅA123", []],
    ["ÄA123", []],
    ["ÖA123", []],
    ["ABC", []],
    ["123", []],
    ["A123", []],
]

testdata_edit_dist_plates = [
    [["ABC123", "ABC124"], ["ABC123"]],
    [["ABC123", "ABC135"], ["ABC123", "ABC135"]],
    [["[UNK_CAR_100]", "[UNK_CAR_101]"], ["[UNK_CAR_100]", "[UNK_CAR_101]"]],
]


@pytest.mark.parametrize("plate,expected", testdata_alt_rep)
def test_alt_representation(plate, expected):
    assert get_alt_representation(plate) == expected


@pytest.mark.parametrize("plate,expected", testdata_valid_plates)
def test_valid_plates(plate, expected):
    valid_plates = sorted(get_valid_plates(plate))
    expected_plates = sorted(expected)

    assert len(valid_plates) == len(expected_plates)
    assert all(
        [test_p == exp_p for test_p, exp_p in zip(valid_plates, expected_plates)]
    )


@pytest.mark.parametrize("plates,expected", testdata_edit_dist_plates)
def test_rm_duplicates_1edit_away(plates, expected):
    groomed_plates = rm_duplicates_1edit_away(plates, [])

    assert len(groomed_plates) == len(expected)
    assert all([test_p == exp_p for test_p, exp_p in zip(groomed_plates, expected)])
