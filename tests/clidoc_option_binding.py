# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from collections import defaultdict
from copy import deepcopy
import re
import sys


__all__ = [
    'SYSTEM_EXIT_OFF',
    'PRINT_DOC_OFF',
    'GUIDELINE_8_OFF',
    'clidoc',
]


SYSTEM_EXIT_OFF = 1 << 0
PRINT_DOC_OFF = 1 << 1
GUIDELINE_8_OFF = 1 << 2


def clidoc(argv, flags=0):
    # flags.
    system_exit_off = SYSTEM_EXIT_OFF & flags
    print_doc_off = PRINT_DOC_OFF & flags
    guideline_8_off = GUIDELINE_8_OFF & flags

    def respond_to_error():
        if not print_doc_off:
            print(Info.doc_text)
        if not system_exit_off:
            sys.exit(0)
        return False

    # preprocess input argument.
    argv_prepprocessor = ArgvPreprocessor(
        argv,
        Info.option_to_representative_option,
        Info.bound_options | Info.oom_bound_options,
    )
    argv_prepprocessor.tokenize_argv()
    if not argv_prepprocessor.tokens:
        return respond_to_error()

    # init match state.
    Info.load_tokens(argv_prepprocessor.tokens)
    MatchStateManager.init(MatchState(Info))
    # token match.
    all_match = Info.doc_node.match() and MatchStateManager.all_match()
    if all_match:
        outcome = MatchStateManager.get_outcome()
        if not guideline_8_off:
            split_comma_separated_oom_outcome(outcome)
        return outcome
    else:
        return respond_to_error()


def split_comma_separated_oom_outcome(outcome):
    for key, value in outcome.items():
        if not isinstance(value, list) or not value:
            continue
        # is non-empty string list outcome.
        # try to split the last element.
        text = value.pop()
        value.extend(
            filter(bool, text.split(',')),
        )


# represent outcome of input argument preprocessing.
class Token(object):
    #
    # input argument types:
    # * POSIX_OPTION
    # * GNU_OPTION
    # * COMMAND
    # * GENERAL_ELEMENT
    #
    # AST token types:
    # * POSIX_OPTION
    # * GNU_OPTION
    # * COMMAND
    # * ARGUMENT
    #
    POSIX_OPTION = 0
    GNU_OPTION = 1
    GENERAL_ELEMENT = 2
    COMMAND = 3
    ARGUMENT = 4

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


# store attributes generated by `clidoc` front end.
class Info(object):
    # root of AST.
    doc_node = None

    # `set` of `Token`.
    bound_options = None
    unbound_options = None
    arguments = None
    oom_bound_options = None
    oom_arguments = None
    commands = None

    # `dict` contains mapping from `Token` to string.
    default_values = None
    # `dict` contains mapping from `Token` to `Token`.
    option_to_representative_option = None
    # string of user defined doc.
    doc_text = None

    # shared by all match state object.
    _tokens = None
    _token_skip_table = None

    @classmethod
    def load_tokens(cls, tokens):
        cls._tokens = tokens
        # construct `_token_skip_table`
        cls._token_skip_table = defaultdict(list)
        for index, token in enumerate(tokens):
            cls._token_skip_table[token].append(index)

    @classmethod
    def get_tokens(cls):
        return cls._tokens

    @classmethod
    def get_token(cls, index):
        if index < len(cls._tokens):
            return cls._tokens[index]
        return None

    @classmethod
    def search_match_token_indices(cls, key):
        return cls._token_skip_table.get(key, [])

    @classmethod
    def is_boolean_key(cls, key):
        return key in cls.unbound_options or key in cls.commands

    @classmethod
    def is_string_key(cls, key):
        return key in cls.bound_options or key in cls.arguments

    @classmethod
    def is_string_list_key(cls, key):
        return key in cls.oom_bound_options or key in cls.oom_arguments


# manage match state of input arguments.
class MatchState(object):

    def _add_outcome(self, attr_name, tokens, callback):
        for token in tokens:
            getattr(self, attr_name)[token] = callback(token)

    def _add_boolean_outcome(self, tokens):
        self._add_outcome(
            '_boolean_outcome',
            tokens,
            lambda x: False,
        )

    def _add_string_outcome(self, tokens, default_values):
        self._add_outcome(
            '_string_outcome',
            tokens,
            lambda token: default_values.get(token, ""),
        )

    def _add_string_list_outcome(self, tokens):
        self._add_outcome(
            '_string_list_outcome',
            tokens,
            lambda x: [],
        )

    def __init__(self, InfoCls):
        self._consumed_flags = [False] * len(InfoCls.get_tokens())

        self._boolean_outcome = {}
        self._add_boolean_outcome(InfoCls.unbound_options)
        self._add_boolean_outcome(InfoCls.commands)

        self._string_outcome = {}
        self._add_string_outcome(InfoCls.bound_options, InfoCls.default_values)
        self._add_string_outcome(InfoCls.arguments, InfoCls.default_values)

        self._string_list_outcome = {}
        self._add_string_list_outcome(InfoCls.oom_bound_options)
        self._add_string_list_outcome(InfoCls.oom_arguments)

    def add_boolean_outcome(self, key):
        self._boolean_outcome[key] = True

    def add_string_outcome(self, key, value):
        self._string_outcome[key] = value

    def add_string_list_outcome(self, key, value):
        self._string_list_outcome[key].append(value)

    def set_consumed_flag(self, index):
        self._consumed_flags[index] = True

    def get_consumed_flag(self, index):
        return self._consumed_flags[index]

    def get_first_unconsumed_index(self, start=0):
        for offset, flag in enumerate(self._consumed_flags[start:]):
            if not flag:
                return start + offset
        return None

    def all_match(self):
        return all(self._consumed_flags)

    def get_outcome(self):
        outcome = {}
        outcome.update(self._boolean_outcome)
        outcome.update(self._string_outcome)
        outcome.update(self._string_list_outcome)
        return outcome


class MatchStateManager(object):

    @classmethod
    def init(cls, match_state):
        cls._match_state = match_state
        cls._state_stack = []

    @classmethod
    def all_match(cls):
        return cls._match_state.all_match()

    @classmethod
    def get_outcome(cls):
        outcome = {}
        for token_key, value in cls._match_state.get_outcome().items():
            outcome[token_key.value] = value
        return outcome

    @classmethod
    def push_rollback_point(cls):
        cls._state_stack.append(deepcopy(cls._match_state))

    @classmethod
    def pop_rollback_point(cls):
        return cls._state_stack.pop()

    @classmethod
    def rollback(cls):
        cls._match_state = cls.pop_rollback_point()

    @classmethod
    def _prepare_unconsumed_index(cls, key):
        match_indices = Info.search_match_token_indices(key)
        for index in match_indices:
            if not cls._match_state.get_consumed_flag(index):
                return index

        # state: cannot find a unconsumed match token.
        if Info.is_string_list_key(key) and match_indices:
            # pretend the last matched token is not consumed.
            return match_indices[-1]

        return None

    @classmethod
    def try_to_generate_boolean_outcome(cls, key):
        if not Info.is_boolean_key(key):
            return False

        index = cls._prepare_unconsumed_index(key)
        if index is None:
            return False
        # change match state.
        cls._match_state.add_boolean_outcome(key)
        cls._match_state.set_consumed_flag(index)
        return True

    @classmethod
    def _try_to_generate_outcome_with_value(cls, key, store_key_value_pair):

        def access_argument_token(index):
            token = Info.get_token(index)
            if token is None:
                return False, None
            # 1. GENERAL_ELEMENT or COMMAND.
            # 2. not consumed.
            flag = ((token.type_id == Token.GENERAL_ELEMENT
                     or token.type_id == Token.COMMAND)
                    and not cls._match_state.get_consumed_flag(index))
            value = token.value
            return flag, value

        def access_normal_token(index):
            token = Info.get_token(index)
            if token is None:
                return False, None
            # 1. GENERAL_ELEMENT.
            # 2. not consumed.
            flag = (token.type_id == Token.GENERAL_ELEMENT
                    and not cls._match_state.get_consumed_flag(index))
            value = token.value
            return flag, value

        if key.type_id == Token.ARGUMENT:
            # deal with `ARGUMENT`.
            key_index = cls._match_state.get_first_unconsumed_index()
            if key_index is None:
                return False
            flag, value = access_argument_token(key_index)
            if flag:
                cls._match_state.set_consumed_flag(key_index)
                store_key_value_pair(key, value)
                return True
        else:
            # deal with other nodes.
            key_index = cls._prepare_unconsumed_index(key)
            if key_index is None:
                return False
            # search the first unconsumed token begins with `key_index` + 1.
            value_index = cls._match_state.get_first_unconsumed_index(
                key_index + 1,
            )
            if value_index is None:
                return False
            flag, value = access_normal_token(value_index)
            if flag:
                cls._match_state.set_consumed_flag(key_index)
                cls._match_state.set_consumed_flag(value_index)
                store_key_value_pair(key, value)
                return True
        return False

    @classmethod
    def try_to_generate_string_outcome(cls, key):
        if not Info.is_string_key(key):
            return False

        return cls._try_to_generate_outcome_with_value(
            key,
            cls._match_state.add_string_outcome,
        )

    @classmethod
    def try_to_generate_string_list_outcome(cls, key):
        if not Info.is_string_list_key(key):
            return False

        return cls._try_to_generate_outcome_with_value(
            key,
            cls._match_state.add_string_list_outcome,
        )


# Implement classes representing following classes:
#
# Terminals:
#   * PosixOption
#   * GnuOption
#   * Command
#   * Argument
#
# Non-terminals:
#   * Doc
#   * LogicAnd
#   * LogicXor
#   * LogicOr
#   * LogicOptional
#   * LogicOneOrMore
class Terminal(object):
    # derived class should override this attribute.
    _type_id = None

    def __init__(self, value):
        self._value = value
        self._children = []

    # generate token for matching.
    def token(self):
        return Token(self._type_id, self._value)

    def _match(self, callbacks):
        key = self.token()
        for callback in callbacks:
            if callback(key):
                return True
        return False

    # return True indicates successfully match, False otherwise.
    def match(self):
        raise Exception("Terminal")


class PosixOption(Terminal):
    _type_id = Token.POSIX_OPTION

    def match(self):
        callbacks = [
            MatchStateManager.try_to_generate_boolean_outcome,
            MatchStateManager.try_to_generate_string_outcome,
            MatchStateManager.try_to_generate_string_list_outcome,
        ]
        return self._match(callbacks)


class GnuOption(Terminal):
    _type_id = Token.GNU_OPTION

    def match(self):
        callbacks = [
            MatchStateManager.try_to_generate_boolean_outcome,
            MatchStateManager.try_to_generate_string_outcome,
            MatchStateManager.try_to_generate_string_list_outcome,
        ]
        return self._match(callbacks)


class Command(Terminal):
    _type_id = Token.COMMAND

    def match(self):
        callbacks = [
            MatchStateManager.try_to_generate_boolean_outcome,
        ]
        return self._match(callbacks)


class Argument(Terminal):
    _type_id = Token.ARGUMENT

    def match(self):
        callbacks = [
            MatchStateManager.try_to_generate_string_outcome,
            MatchStateManager.try_to_generate_string_list_outcome,
        ]
        return self._match(callbacks)


class NonTerminal(object):
    def __init__(self):
        self._children = []

    def add_child(self, child):
        self._children.append(child)

    # in case the node has only one child, return it.
    def get_forward_child(self):
        return self._children[0]

    # return True indicates successfully match, False otherwise.
    def match(self):
        raise Exception("NonTerminal")


class Doc(NonTerminal):

    def match(self):
        return self.get_forward_child().match()


class LogicAnd(NonTerminal):

    def match(self):
        MatchStateManager.push_rollback_point()
        for child in self._children:
            if not child.match():
                MatchStateManager.rollback()
                return False
        MatchStateManager.pop_rollback_point()
        return True


class LogicXor(NonTerminal):

    def match(self):
        for child in self._children:
            if child.match():
                return True
        return False


class LogicOr(NonTerminal):

    def match(self):
        one_or_more = False
        for child in self._children:
            if child.match():
                one_or_more = True
        return one_or_more


class LogicOptional(NonTerminal):

    def match(self):
        self.get_forward_child().match()
        return True


class LogicOneOrMore(NonTerminal):

    def match(self):
        child = self.get_forward_child()
        counter = -1
        while True:
            counter = counter + 1
            if not child.match():
                break
        return counter > 0


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
        self._argv = []
        for arg in argv[1:]:
            arg = arg.decode('utf-8') if hasattr(arg, 'decode') else arg
            self._argv.append(arg)

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
        equal_sign_index = value.find('=')
        if equal_sign_index not in [-1, len(value) - 1]:
            option = self._get_rep_option(
                Token.GNU_OPTION,
                value[:equal_sign_index],
            )
            if option and self._option_is_bound(option):
                # find it!
                self.tokens.append(option)
                self._add_general_element(value[equal_sign_index + 1:])
                split_flag = True
        if not split_flag:
            self._add_general_element(value)
        return False

    def _process_unknow_case(self, value):
        if value == '--':
            return True
        suspect_command = Token(Token.COMMAND, value)
        if suspect_command in Info.commands:
            self.tokens.append(suspect_command)
        else:
            self._add_general_element(value)
        return False

    def _fill_tokens(self):
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

    def _correct_oom_argument_type(self):
        is_oom_bound_option_argument = False
        for token in self.tokens:
            is_oom_bound_option = token in Info.oom_bound_options
            if is_oom_bound_option and not is_oom_bound_option_argument:
                is_oom_bound_option_argument = True
                continue
            if not is_oom_bound_option and is_oom_bound_option_argument:
                token.type_id = Token.GENERAL_ELEMENT
                continue
            if is_oom_bound_option and is_oom_bound_option_argument:
                is_oom_bound_option_argument = False
                continue

    def tokenize_argv(self):
        self._fill_tokens()
        self._correct_oom_argument_type()


#####################
#####  codegen  #####
#####################
Info.bound_options = set([
    Token(Token.GNU_OPTION, "--long-1"),
    Token(Token.GNU_OPTION, "--long-2"),
    Token(Token.POSIX_OPTION, "-a"),
    Token(Token.POSIX_OPTION, "-b"),
])
Info.unbound_options = set([
    Token(Token.GNU_OPTION, "--long-4"),
    Token(Token.POSIX_OPTION, "-c"),
])
Info.arguments = set([
    Token(Token.ARGUMENT, "<p3>"),
])
Info.oom_bound_options = set([
    Token(Token.GNU_OPTION, "--long-3"),
    Token(Token.POSIX_OPTION, "-d"),
    Token(Token.POSIX_OPTION, "-e"),
])
Info.oom_arguments = set([
])
Info.commands = set([
    Token(Token.COMMAND, "command"),
])
Info.default_values = {
}
Info.option_to_representative_option = {
    Token(Token.GNU_OPTION, "--long-1"): Token(Token.GNU_OPTION, "--long-1"),
    Token(Token.GNU_OPTION, "--long-2"): Token(Token.GNU_OPTION, "--long-2"),
    Token(Token.GNU_OPTION, "--long-3"): Token(Token.GNU_OPTION, "--long-3"),
    Token(Token.GNU_OPTION, "--long-4"): Token(Token.GNU_OPTION, "--long-4"),
    Token(Token.POSIX_OPTION, "-a"): Token(Token.POSIX_OPTION, "-a"),
    Token(Token.POSIX_OPTION, "-b"): Token(Token.POSIX_OPTION, "-b"),
    Token(Token.POSIX_OPTION, "-c"): Token(Token.POSIX_OPTION, "-c"),
    Token(Token.POSIX_OPTION, "-d"): Token(Token.POSIX_OPTION, "-d"),
    Token(Token.POSIX_OPTION, "-e"): Token(Token.POSIX_OPTION, "-e"),
    Token(Token.POSIX_OPTION, "-f"): Token(Token.GNU_OPTION, "--long-4"),
}
_t0 = PosixOption("-a")
_t1 = PosixOption("-b")
_t2 = PosixOption("-c")
_t3 = Argument("<p3>")
_nt4 = LogicAnd()
_nt4.add_child(_t2)
_nt4.add_child(_t3)
_t7 = PosixOption("-d")
_nt8 = LogicOneOrMore()
_nt8.add_child(_t7)
_t10 = PosixOption("-e")
_nt11 = LogicOneOrMore()
_nt11.add_child(_t10)
_t13 = Command("command")
_t14 = GnuOption("--long-1")
_t15 = GnuOption("--long-2")
_t16 = GnuOption("--long-3")
_nt17 = LogicOneOrMore()
_nt17.add_child(_t16)
_t19 = PosixOption("-f")
_t20 = GnuOption("--long-4")
_nt21 = LogicXor()
_nt21.add_child(_t0)
_nt21.add_child(_t1)
_nt21.add_child(_nt4)
_nt21.add_child(_nt8)
_nt21.add_child(_nt11)
_nt21.add_child(_t13)
_nt21.add_child(_t14)
_nt21.add_child(_t15)
_nt21.add_child(_nt17)
_nt21.add_child(_t19)
_nt21.add_child(_t20)
_nt33 = Doc()
_nt33.add_child(_nt21)

Info.doc_node = _nt33
Info.doc_text = '''Usage:
  utility_name -a <p1>
  utility_name -bP2
  utility_name -c <p3>  -c not bound.
  utility_name -d <p4>...
  utility_name -eP5...
  utility_name command

  utility_name --long-1=<g1>
  utility_name --long-2 <g2>
  utility_name --long-3=<g3>...

  utility_name -f|--long-4

Options:
  -a <p1>
	-b P2
  -d <p4>
  -e P5
  --long-2=<g2>
	-f,--long-4
'''
