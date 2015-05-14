# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_command import *
from utils import generate_key_checker, CLIDOC_TEST_MODE


key_checker = generate_key_checker(
    {
        "command",
        "what-ever",
    },
    set(),
    set(),
)


def test_run():
    outcome = clidoc(
        ["utility_name", "command"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["command"]

    outcome = clidoc(
        ["utility_name", "what-ever"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["what-ever"]


def test_fail():
    assert not clidoc(
        ["utility_name", "COMMAND"],
        CLIDOC_TEST_MODE,
    )
    assert not clidoc(
        ["utility_name", "command", "something else"],
        CLIDOC_TEST_MODE,
    )
