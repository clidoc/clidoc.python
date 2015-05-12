# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from clidoc.codegen import (Token, ArgvPreprocessor, Info, MatchStateManager,
                            MatchState)


# init info.
Info.unbound_options = [Token(Token.POSIX_OPTION, '-a')]
Info.commands = [Token(Token.COMMAND, 'command')]

Info.bound_options = [Token(Token.GNU_OPTION, '--foo')]
Info.arguments = [Token(Token.ARGUMENT, '<arg>')]

Info.oom_bound_options = [Token(Token.POSIX_OPTION, '-b')]
Info.oom_arguments = [Token(Token.ARGUMENT, 'BAR')]

Info.default_values = {Token(Token.ARGUMENT, 'BAR'): "42"}

Info.load_tokens([
    Token(Token.POSIX_OPTION, '-a'),
    Token(Token.POSIX_OPTION, '-b'),
    Token(Token.GENERAL_ELEMENT, 'foobar'),
    Token(Token.GENERAL_ELEMENT, 'foobar'),
    Token(Token.POSIX_OPTION, '-b'),
])


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


def test_info():
    assert Info.is_boolean_key(
        Token(Token.POSIX_OPTION, '-a'),
    )
    assert Info.is_boolean_key(
        Token(Token.COMMAND, 'command'),
    )
    assert Info.is_string_key(
        Token(Token.GNU_OPTION, '--foo'),
    )
    assert Info.is_string_key(
        Token(Token.ARGUMENT, '<arg>'),
    )
    assert Info.is_string_list_key(
        Token(Token.POSIX_OPTION, '-b'),
    )
    assert Info.is_string_list_key(
        Token(Token.ARGUMENT, 'BAR'),
    )
    assert [1, 4] == Info.search_match_token_indices(
        Token(Token.POSIX_OPTION, '-b'),
    )
    assert [2, 3] == Info.search_match_token_indices(
        Token(Token.GENERAL_ELEMENT, 'foobar'),
    )
    assert [] == Info.search_match_token_indices(
        Token(Token.GENERAL_ELEMENT, 'not exist'),
    )


def test_match_state_manager_state_change():
    MatchStateManager.init(MatchState(Info))
    assert not any(MatchStateManager._match_state._consumed_flags)
    MatchStateManager.push_rollback_point()
    MatchStateManager._match_state._consumed_flags[0] = True
    assert any(MatchStateManager._match_state._consumed_flags)
    MatchStateManager.rollback()
    assert not any(MatchStateManager._match_state._consumed_flags)
