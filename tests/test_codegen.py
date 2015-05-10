# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc.codegen import Token, ArgvPreprocessor


def test_tokenization():
    option_to_rep_option = {
        Token(Token.POSIX_OPTION, "-c"): Token(Token.GNU_OPTION, "--longc"),
        Token(Token.GNU_OPTION, "--longc"): Token(Token.GNU_OPTION, "--longc"),
        Token(Token.GNU_OPTION, "--long-option"):
        Token(Token.GNU_OPTION, "--long-option"),
        Token(Token.POSIX_OPTION, "-f"): Token(Token.POSIX_OPTION, "-f"),
        Token(Token.POSIX_OPTION, "-o"): Token(Token.POSIX_OPTION, "-o"),
        Token(Token.POSIX_OPTION, "-I"): Token(Token.POSIX_OPTION, "-I"),
    }

    bound_options = {
        Token(Token.POSIX_OPTION, "-o"),
        Token(Token.POSIX_OPTION, "-I"),
        Token(Token.GNU_OPTION, "--long-option"),
    }

    argv = [
        "utility_name",

        "-c",
        "whatever",
        "1 2 3 a b c",

        "-I/usr/whatever",
        "--long-option=!@$*$",

        "-I",
        "--long-option=whatever",

        "-foFILE",

        "--",
        "-c",
        "--long",
    ]
    preprocessor = ArgvPreprocessor(argv, option_to_rep_option, bound_options)
    preprocessor.tokenize_argv()

    expected = [
        Token(Token.GNU_OPTION, '--longc'),
        Token(Token.GENERAL_ELEMENT, 'whatever'),
        Token(Token.GENERAL_ELEMENT, '1 2 3 a b c'),

        Token(Token.POSIX_OPTION, '-I'),
        Token(Token.GENERAL_ELEMENT, '/usr/whatever'),

        Token(Token.GNU_OPTION, '--long-option'),
        Token(Token.GENERAL_ELEMENT, '!@$*$'),

        Token(Token.POSIX_OPTION, '-I'),
        Token(Token.GENERAL_ELEMENT, '--long-option=whatever'),

        Token(Token.POSIX_OPTION, '-f'),
        Token(Token.POSIX_OPTION, '-o'),
        Token(Token.GENERAL_ELEMENT, 'FILE'),

        Token(Token.GENERAL_ELEMENT, '-c'),
        Token(Token.GENERAL_ELEMENT, '--long'),
    ]
    assert expected == preprocessor.tokens
