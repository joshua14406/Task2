"""
15 checks for the Task 2 automata, each against an independent reference:
Python's ipaddress-style integer rule, regular expressions, and a plain Luhn
implementation.
"""
import random
import re
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fa_checks.automata import all_strings, equivalent  # noqa: E402
from fa_checks.validators import (  # noqa: E402
    APPLICATIONS, CARD_DFA, CARD_LUHN_DFA, CARD_NFA, CARD_REGEX, CARD_SUBSET, HOLDER_TYPES,
    IP_EXACT_DFA, IP_SHAPE_DFA, PAN_DFA, PAN_SHAPE_DFA, card_reference, ip_reference, luhn_ok)


def test_listed_examples():                                           # 1
    for key, app in APPLICATIONS.items():
        assert len(app["accept"]) >= 5 and len(app["reject"]) >= 5, key
        for s in app["accept"]:
            assert app["dfa"].accepts(s), (key, s)
        for s in app["reject"]:
            assert not app["dfa"].accepts(s), (key, s)


def test_ip_shape_exhaustive():                                       # 2
    """All 349 525 strings up to length 9 over {1, 0, ., x}."""
    rx = re.compile(r"\d{1,3}(\.\d{1,3}){3}")
    count = 0
    for s in all_strings("10.x", 9):
        count += 1
        assert IP_SHAPE_DFA.accepts(s) == bool(rx.fullmatch(s)), s
    assert count == 349525


def test_ip_exact_every_octet_and_neighbours():                       # 3
    """Every string of 1-3 digits (1 110 of them) in every one of the four positions."""
    octets = [str(d) for d in range(10)] + [f"{n:02d}" for n in range(100)] + \
             [f"{n:03d}" for n in range(1000)]
    for o in octets:
        for pos in range(4):
            parts = ["1", "1", "1", "1"]
            parts[pos] = o
            s = ".".join(parts)
            assert IP_EXACT_DFA.accepts(s) == ip_reference(s), s


def test_ip_random_strings():                                         # 4
    rnd = random.Random(273)
    pool = "0125.9"
    for _ in range(60000):
        s = "".join(rnd.choice(pool) for _ in range(rnd.randint(6, 16)))
        assert IP_EXACT_DFA.accepts(s) == ip_reference(s), s


def test_pan_against_regex():                                         # 5
    rx = re.compile(r"[A-Z]{3}[" + HOLDER_TYPES + r"][A-Z]\d{4}[A-Z]")
    rnd = random.Random(2155)
    pool = string.ascii_uppercase + string.digits + "a "
    for _ in range(80000):
        if rnd.random() < 0.5:
            s = "".join(rnd.choice(string.ascii_uppercase) for _ in range(5)) + \
                f"{rnd.randint(0, 9999):04d}" + rnd.choice(string.ascii_uppercase)
        else:
            s = "".join(rnd.choice(pool) for _ in range(rnd.randint(8, 11)))
        assert PAN_DFA.accepts(s) == bool(rx.fullmatch(s)), s


def test_pan_holder_rule_costs_no_state():                            # 6
    assert PAN_SHAPE_DFA.size() == PAN_DFA.size() == 12
    assert PAN_SHAPE_DFA.accepts("ABCDE1234F") and not PAN_DFA.accepts("ABCDE1234F")


def test_card_format_exhaustive_class_strings():                      # 7
    """All 27 ways of joining four 4-digit groups with nothing, a space or a hyphen."""
    rx = re.compile(CARD_REGEX)
    seps = ["", " ", "-"]
    for a in seps:
        for b in seps:
            for c in seps:
                s = "1234" + a + "5678" + b + "9012" + c + "3456"
                assert CARD_DFA.accepts(s) == bool(rx.fullmatch(s)), s
                assert CARD_NFA.accepts(s) == bool(rx.fullmatch(s)), s


def test_card_format_random():                                        # 8
    rx = re.compile(CARD_REGEX)
    rnd = random.Random(16)
    for _ in range(60000):
        groups = ["".join(rnd.choice("0123456789") for _ in range(rnd.choice([3, 4, 4, 4, 5])))
                  for _ in range(rnd.choice([3, 4, 4, 5]))]
        sep = rnd.choice(["", " ", "-"])
        s = sep.join(groups)
        if rnd.random() < 0.2 and len(s) > 5:
            k = rnd.randrange(len(s))
            s = s[:k] + rnd.choice(" -x") + s[k + 1:]
        assert CARD_DFA.accepts(s) == bool(rx.fullmatch(s)), s
        assert CARD_NFA.accepts(s) == bool(rx.fullmatch(s)), s


def test_card_subset_minimal_equivalent():                            # 9
    same, counterexample = equivalent(CARD_SUBSET, CARD_DFA)
    assert same, counterexample
    merged = [m for m, members in CARD_DFA.members.items() if len(members) == 3]
    assert len(merged) == 5                         # the last group (and the end) is shared


def test_luhn_against_reference():                                    # 10
    rnd = random.Random(10)
    for _ in range(40000):
        digits = "".join(rnd.choice(string.digits) for _ in range(15))
        check = rnd.choice(string.digits)
        number = digits + check
        sep = rnd.choice(["", " ", "-"])
        s = sep.join(number[i:i + 4] for i in range(0, 16, 4))
        assert CARD_LUHN_DFA.accepts(s) == luhn_ok(number), s


def test_luhn_exactly_one_check_digit():                              # 11
    rnd = random.Random(11)
    for _ in range(2000):
        body = "".join(rnd.choice(string.digits) for _ in range(15))
        good = [d for d in string.digits if CARD_LUHN_DFA.accepts(body + d)]
        assert len(good) == 1


def test_luhn_detects_single_digit_errors():                          # 12
    base = "4111111111111111"
    for i in range(16):
        for d in string.digits:
            if d != base[i]:
                assert not CARD_LUHN_DFA.accepts(base[:i] + d + base[i + 1:])


def test_state_counts_match_report():                                 # 13
    assert (IP_SHAPE_DFA.size(), IP_EXACT_DFA.size()) == (17, 25)
    assert (len(CARD_NFA.states), CARD_SUBSET.size(), CARD_DFA.size(), CARD_LUHN_DFA.size()) \
        == (55, 48, 38, 353)


def test_value_rules_refine_shapes():                                 # 14
    rnd = random.Random(14)
    for _ in range(20000):
        s = ".".join(str(rnd.randint(0, 400)) for _ in range(4))
        if IP_EXACT_DFA.accepts(s):
            assert IP_SHAPE_DFA.accepts(s)
        t = "".join(rnd.choice(string.digits) for _ in range(16))
        assert CARD_LUHN_DFA.accepts(t) == card_reference(t, True)


def test_minimal_dfas_are_really_minimal():                           # 15
    for dfa in (IP_EXACT_DFA, CARD_DFA, CARD_LUHN_DFA):
        assert dfa.minimise().size() == dfa.size()
