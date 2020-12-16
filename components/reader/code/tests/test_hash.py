# -*- coding: utf-8 -*-
from hasher import create_hash


def test_hash_differs_from_input():
    assert create_hash("ABC123") != "ABC123"


def test_hash_length():
    assert len(create_hash("ABC123")) == 24
