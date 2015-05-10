# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import re


class Token(object):
    # types of input arguments.
    POSIX_OPTION = 0
    GNU_OPTION = 1
    COMMAND = 2
    GENERAL_ELEMENT = 3

    def __init__(self, type_id, value):
        self.type_id = type_id
        self.value = value

    def __eq__(self, other):
        return (self.type_id == other.type_id
                and self.value == other.value)

    def __hash__(self):
        # for dict and set.
        return hash(self.type_id) ^ hash(self.value)

    def __repr__(self):
        return '<Token ({0}, {1})>'.format(self.type_id, self.value)


# manage match state of input arguemnts.
class MatchStateManager(object):
    pass


class SimpleMemento(object):
    pass


# Implement classes representing following classes:
#
# Non-terminals:
#   * Doc
#   * LogicAnd
#   * LogicXor
#   * LogicOr
#   * LogicOptional
#   * LogicOneOrMore
#
# Terminals:
#   * PosixOption
#   * GnuOption
#   * Argument
#   * Command
class BaseNode(object):
    # derived class should override this attribute.
    _type_id = None

    def __init__(self, value):
        self._value = value
        self._children = []

    def token(self):
        return Token(self._type_id, self._value)

    def add_child(self, child):
        self._children.append(child)

    # return True indicates successfully match, False otherwise.
    def match(self):
        raise Exception("BaseNode")


# preprocessing algorithm of input arguments.
# return a list of tokens.
class ArgvPreprocessor(object):
    POSIX_OPTION = 0
    GNU_OPTION = 1
    SINGLE_DASH_CASE = 2
    DOUBLE_DASH_CASE = 3
    UNKNOW_CASE = 4

    # `argv`: input argument vector.
    # `option_to_rep_option`: a dict contains mapping from option to its
    # representative option.
    # `bound_options`: a set of bound options.
    def __init__(self, argv, option_to_rep_option, bound_options):
        # ignore `argv[0]`.
        self._argv = argv[1:]
        self._option_to_rep_option = option_to_rep_option
        self._bound_options = bound_options
        # preprocessed input arguments.
        self.tokens = []

    def _detect_argument_pattern(self, value):
        # patterns.
        ALNUM = '[a-zA-Z0-9]'
        POSIX_OPTION_PATTERN = '^\\-{}$'.format(ALNUM)
        GNU_OPTION_PATTERN = '^\\-\\-{0}({0}|\\-)+$'.format(ALNUM)

        if re.match(POSIX_OPTION_PATTERN, value):
            return self.POSIX_OPTION
        if re.match(GNU_OPTION_PATTERN, value):
            return self.GNU_OPTION
        # state: not `POSIX_OPTION` or `GNU_OPTION`.
        if len(value) <= 2:
            return self.UNKNOW_CASE
        # state: not `POSIX_OPTION` or `GNU_OPTION`.
        #        len(value) > 2.
        if value.startswith('--'):
            return self.DOUBLE_DASH_CASE
        # state: not `POSIX_OPTION` or `GNU_OPTION`.
        #        len(value) > 2.
        #        not startswith "--".
        if value.startswith('-'):
            return self.SINGLE_DASH_CASE
        # state: not `POSIX_OPTION` or `GNU_OPTION`.
        #        len(value) > 2.
        #        not startswith "-".
        return self.UNKNOW_CASE

    def _get_rep_option(self, type_id, value):
        return self._option_to_rep_option.get(Token(type_id, value), None)

    def _option_is_bound(self, option):
        return option in self._bound_options

    def _add_general_element(self, value, dst=None):
        dst = dst or self.tokens
        dst.append(
            Token(Token.GENERAL_ELEMENT, value),
        )

    def _process_option(self, type_id, value):
        option = self._get_rep_option(type_id, value)
        if option is None:
            self._add_general_element(value)
            return False
        # state: valid option.
        self.tokens.append(option)
        if self._option_is_bound(option):
            return True
        return False

    def _process_posix_option(self, value):
        return self._process_option(Token.POSIX_OPTION, value)

    def _process_gnu_option(self, value):
        return self._process_option(Token.GNU_OPTION, value)

    def _process_single_dash_case(self, value):
        # ignore '-'.
        chars = value[1:]
        tokens_cache = []

        skip_next_argument = False
        cur_char_index = 0
        for char in chars:
            option = self._get_rep_option(Token.POSIX_OPTION, '-' + char)
            if option is None:
                break
            # state: valid option.
            tokens_cache.append(option)
            if self._option_is_bound(option):
                if cur_char_index != len(chars) - 1:
                    # `char` is not the last character.
                    self._add_general_element(
                        chars[cur_char_index + 1:],
                        tokens_cache,
                    )
                else:
                    # `char` is the last character.
                    skip_next_argument = True
                # mark consumed all characters.
                cur_char_index = len(chars)
                break
            cur_char_index = cur_char_index + 1
        # check if word splitting is successful.
        if cur_char_index == len(chars):
            # merge change.
            self.tokens.extend(tokens_cache)
        else:
            self._add_general_element(value)
        return skip_next_argument

    def _process_double_dash_case(self, value):
        split_flag = False
        equal_sign_index = 0
        while True:
            equal_sign_index = value.find('=', equal_sign_index)
            if equal_sign_index in [-1, len(value) - 1]:
                # 1. cannot found '='.
                # 2. '=' is the last character.
                break

            # state: "=" is not the last character.
            option = self._get_rep_option(
                Token.GNU_OPTION,
                value[:equal_sign_index],
            )
            if option and self._option_is_bound(option):
                # find it!
                self.tokens.append(option)
                self._add_general_element(value[equal_sign_index + 1:])
                split_flag = True
                break
            # not a valid split, re-search "=" again.
            equal_sign_index = equal_sign_index + 1
        if not split_flag:
            self._add_general_element(value)
        return False

    def _process_unknow_case(self, value):
        if value == '--':
            return True
        self._add_general_element(value)
        return False

    def tokenize_argv(self):
        case_function_mapping = {
            self.POSIX_OPTION: self._process_posix_option,
            self.GNU_OPTION: self._process_gnu_option,
            self.SINGLE_DASH_CASE: self._process_single_dash_case,
            self.DOUBLE_DASH_CASE: self._process_double_dash_case,
            self.UNKNOW_CASE: self._process_unknow_case,
        }
        skip_next_argument = False
        for index, value in enumerate(self._argv):
            if skip_next_argument:
                self._add_general_element(value)
                skip_next_argument = False
                continue
            # process `value`.
            case = self._detect_argument_pattern(value)
            function = case_function_mapping[case]
            flag = function(value)
            if case != self.UNKNOW_CASE:
                skip_next_argument = flag
                continue
            # check if detecting "--".
            if case == self.UNKNOW_CASE and flag:
                for value_after_double_dash in self._argv[index + 1:]:
                    self._add_general_element(value_after_double_dash)
                break
