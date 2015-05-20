# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_argument import *
from utils import generate_key_checker, CLIDOC_TEST_MODE


key_checker = generate_key_checker(
    {
        "flag-1",
        "flag-2",
        "command1",
        "command2",
    },
    {
        "ARG1",
        "<arg2>",
    },
    {
        "<arg3>",
    },
)


def test_arg1():
    outcome = clidoc(
        ["utility_name", "flag-1", "value"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "value" == outcome["ARG1"]


def test_arg2():
    outcome = clidoc(
        ["utility_name", "flag-2", "value"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "value" == outcome["<arg2>"]


def test_arg3():
    outcome = clidoc(
        ["utility_name", "a", "b", "c"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["a", "b", "c"] == outcome["<arg3>"]

    outcome = clidoc(
        ["utility_name", "command1", "a"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["command1", "a"] == outcome["<arg3>"]

    outcome = clidoc(
        ["utility_name", "flag-1", "a", "b"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert ["flag-1", "a", "b"] == outcome["<arg3>"]
