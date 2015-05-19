# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_default_value import *
from utils import generate_key_checker, CLIDOC_TEST_MODE


key_checker = generate_key_checker(
    {
        "flag-a",
        "flag-arg2",
    },
    {
        "-a",
        "<arg2>",
    },
    set(),
)


def test_option_a():
    outcome = clidoc(
        ["utility_name", "flag-a"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "42" == outcome["-a"]


def test_arg2():
    outcome = clidoc(
        ["utility_name", "flag-arg2"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert "43" == outcome["<arg2>"]
