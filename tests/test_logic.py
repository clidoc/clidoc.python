# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_logic import *
from utils import generate_key_checker, CLIDOC_TEST_MODE


key_checker = generate_key_checker(
    {
        "-a", "-b", "-c",
        "-d", "-e", "-f",
        "-g",
        "-h", "flag_h",
        "-i", "-j",
        "-k", "-l", "-m", "-n",
        "-o", "-p", "-q", "-r", "flag_opqr",
    },
    set(),
    set(),
)


def test_abc():
    outcome = clidoc(
        ["utility_name", "-a", "-b", "-c"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-a"]
    assert outcome["-b"]
    assert outcome["-c"]

    outcome = clidoc(
        ["utility_name", "-abc"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-a"]
    assert outcome["-b"]
    assert outcome["-c"]


def test_def():
    outcome = clidoc(
        ["utility_name", "-d", "-e", "-f"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-d"]
    assert outcome["-e"]
    assert outcome["-f"]

    outcome = clidoc(
        ["utility_name", "-fed"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-d"]
    assert outcome["-e"]
    assert outcome["-f"]


def test_g():
    outcome = clidoc(
        ["utility_name", "-g"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-g"]


def test_h():
    outcome = clidoc(
        ["utility_name", "flag_h"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert not outcome["-h"]


def test_ij():
    outcome = clidoc(
        ["utility_name", "-i"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-i"]

    assert not clidoc(
        ["utility_name", "-ij"],
        CLIDOC_TEST_MODE,
    )


def test_klmn():
    outcome = clidoc(
        ["utility_name", "-klmn"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-k"]
    assert outcome["-l"]
    assert outcome["-m"]
    assert outcome["-n"]

    assert not clidoc(
        ["utility_name", "-kmn"],
        CLIDOC_TEST_MODE,
    )
    assert not clidoc(
        ["utility_name", "-lmn"],
        CLIDOC_TEST_MODE,
    )


def test_opqr():
    outcome = clidoc(
        ["utility_name", "-opqr", "flag_opqr"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-o"]
    assert outcome["-p"]
    assert outcome["-q"]
    assert outcome["-r"]

    outcome = clidoc(
        ["utility_name", "-or", "flag_opqr"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert outcome["-o"]
    assert not outcome["-p"]
    assert not outcome["-q"]
    assert outcome["-r"]

    outcome = clidoc(
        ["utility_name", "flag_opqr"],
        CLIDOC_TEST_MODE,
    )
    key_checker(outcome)
    assert not outcome["-o"]
    assert not outcome["-p"]
    assert not outcome["-q"]
    assert not outcome["-r"]

    assert not clidoc(
        ["utility_name", "-pq"],
        CLIDOC_TEST_MODE,
    )
    assert not clidoc(
        ["utility_name", "-opr"],
        CLIDOC_TEST_MODE,
    )
