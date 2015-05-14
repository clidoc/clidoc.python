# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_simple_option import *
from utils import generate_key_checker, CLIDOC_TEST_MODE


key_checker = generate_key_checker(
    {
        "-a",
        "--long-1",
    },
    set(),
    set(),
)


def test_option_a():
    outcome = clidoc(
        ["utility_name", "-a"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-a"]


def test_option_long_1():
    outcome = clidoc(
        ["utility_name", "--long-1"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["--long-1"]
