# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc_simple_option import *

CLIDOC_TEST_MODE = SYSTEM_EXIT_OFF | PRINT_DOC_OFF


def generate_key_checker(boolean_keys, string_keys, string_list_keys):
    assert type(boolean_keys) == set
    assert type(string_keys) == set
    assert type(string_list_keys) == set

    def check_outcome(outcome):
        assert outcome
        expected_keys = boolean_keys | string_keys | string_list_keys
        assert expected_keys == set(outcome.keys())
    return check_outcome
