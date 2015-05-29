# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_option_binding import *
from utils import generate_key_checker, CLIDOC_TEST_MODE


key_checker = generate_key_checker(
    {
        "-c",
        "--long-4",
        "command",
    },
    {
        "-a",
        "-b",
        "--long-1",
        "--long-2",
        "<p3>",
    },
    {
        "-d",
        "-e",
        "--long-3",
    },
)


def test_option_a():
    outcome = clidoc(
        ["utility_name", "-a", "value"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "value" == outcome["-a"]


def test_option_b():
    outcome = clidoc(
        ["utility_name", "-b", "value"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "value" == outcome["-b"]


def test_option_c_p3():
    outcome = clidoc(
        ["utility_name", "-c", "value"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-c"]
    assert "value" == outcome["<p3>"]


def test_option_e():
    outcome = clidoc(
        ["utility_name", "-e", "a", "b", "c"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "b", "c"] == outcome["-e"]

    outcome = clidoc(
        ["utility_name", "-e", "a", "-eb", "-ec"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "b", "c"] == outcome["-e"]

    outcome = clidoc(
        ["utility_name", "-e", "a", "command", "b"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "command", "b"] == outcome["-e"]

    outcome = clidoc(
        ["utility_name", "-e", "a", "command", "-e", "b", "c"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "b", "c"] == outcome["-e"]
    assert outcome["command"]


def test_guideline_8():
    outcome = clidoc(
        ["utility_name", "-e", "a,b,,c,"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "b", "c"] == outcome["-e"]

    outcome = clidoc(
        ["utility_name", "-e", "a,b,,c,"],
        CLIDOC_TEST_MODE | GUIDELINE_8_OFF,
    )
    key_checker(outcome)
    assert ["a,b,,c,"] == outcome["-e"]

    outcome = clidoc(
        ["utility_name", "-e", "c,d", "-e", "a,b,,c,"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["c,d", "a,b,,c,"] == outcome["-e"]


def test_option_long_1():
    outcome = clidoc(
        ["utility_name", "--long-1", "!@#^&$!"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "!@#^&$!" == outcome["--long-1"]


def test_option_long_2():
    outcome = clidoc(
        ["utility_name", "--long-2", "!@#^&$!"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "!@#^&$!" == outcome["--long-2"]


def test_option_long_3():
    outcome = clidoc(
        ["utility_name", "--long-3", "a", "b", "c"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "b", "c"] == outcome["--long-3"]


def test_option_long_4():
    outcome = clidoc(
        ["utility_name", "-f"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["--long-4"]

    outcome = clidoc(
        ["utility_name", "--long-4"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["--long-4"]
