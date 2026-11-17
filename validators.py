"""
The three Task 2 applications.

  1. IPv4 address        - shape DFA (1-3 digits per part) vs exact octet DFA (0-255,
                           no leading zeros)
  2. PAN card number     - DFA over well-chosen classes; the holder-type rule is free
  3. Debit-card number   - NFA that guesses the grouping style (none / spaces / hyphens)
                           -> subset construction -> minimal DFA; Luhn checksum as a
                           regular value rule
"""
import string

from .automata import DFA, NFA

# ===========================================================================
# 1. IPv4 address
# ===========================================================================
IP_ALPHA = ["D", "DOT", "O"]


def ip_class(ch):
    if ch in string.digits:
        return "D"
    return "DOT" if ch == "." else "O"


def _ip_shape():
    """Four parts of 1-3 digits separated by dots."""
    delta = {}
    for part in range(4):
        base = f"p{part}"
        for k in range(3):                       # k digits read in this part
            delta[(f"{base}_{k}", "D")] = f"{base}_{k + 1}"
        if part < 3:
            for k in (1, 2, 3):
                delta[(f"{base}_{k}", "DOT")] = f"p{part + 1}_0"
    states = [f"p{p}_{k}" for p in range(4) for k in range(4)]
    return DFA("IPv4 (shape)", IP_ALPHA, delta, "p0_0", {"p3_1", "p3_2", "p3_3"}, ip_class,
               states=states)


IP_SHAPE_DFA = _ip_shape()

RAW_IP_ALPHA = list(string.digits) + [".", "other"]


def raw_ip_class(ch):
    return ch if ch in string.digits + "." else "other"


VALID_OCTETS = [str(n) for n in range(256)]          # "0".."255", no leading zeros


def _ip_exact():
    """A trie over the 256 valid octets, repeated four times, then minimised."""
    delta = {}
    for part in range(4):
        for octet in VALID_OCTETS:
            for k in range(len(octet)):
                delta[(f"o{part}:{octet[:k]}", octet[k])] = f"o{part}:{octet[:k + 1]}"
            if part < 3:
                delta[(f"o{part}:{octet}", ".")] = f"o{part + 1}:"
    acc = {f"o3:{o}" for o in VALID_OCTETS}
    raw = DFA("IPv4 (exact octets)", RAW_IP_ALPHA, delta, "o0:", acc, raw_ip_class)
    return raw.minimise("IPv4 (exact octets, minimal)", prefix="i")


IP_EXACT_DFA = _ip_exact()


def ip_reference(s):
    parts = s.split(".")
    return (len(parts) == 4 and all(p.isdigit() and p.isascii() and str(int(p)) == p
                                    and int(p) <= 255 for p in parts))


# ===========================================================================
# 2. PAN card number: AAAAA9999A, 4th letter = holder type
# ===========================================================================
# Holder types: P person, C company, H HUF, F firm, A AOP, T trust, B BOI,
# L local authority, J artificial juridical person, G government.
HOLDER_TYPES = "ABCFGHJLPT"
PAN_ALPHA = ["H", "L", "D", "O"]          # H = holder-type letter, L = other letter


def pan_class(ch):
    if ch in HOLDER_TYPES:
        return "H"
    if ch in string.ascii_uppercase:
        return "L"
    return "D" if ch in string.digits else "O"


def _pan(holder_rule):
    letters = ["H", "L"]
    delta = {}
    for k in range(3):
        for a in letters:
            delta[(f"q{k}", a)] = f"q{k + 1}"
    for a in (["H"] if holder_rule else letters):
        delta[("q3", a)] = "q4"
    for a in letters:
        delta[("q4", a)] = "q5"
    for k in range(5, 9):
        delta[(f"q{k}", "D")] = f"q{k + 1}"
    for a in letters:
        delta[("q9", a)] = "q10"
    name = "PAN (with holder-type rule)" if holder_rule else "PAN (shape only)"
    return DFA(name, PAN_ALPHA, delta, "q0", {"q10"}, pan_class,
               states=[f"q{k}" for k in range(11)])


PAN_SHAPE_DFA = _pan(False)
PAN_DFA = _pan(True)

# ===========================================================================
# 3. Debit-card number: 16 digits, optionally grouped 4-4-4-4 by spaces OR hyphens
# ===========================================================================
CARD_ALPHA = ["D", "SP", "HY", "O"]
CARD_EDGE = {"SP": "␣", "HY": "-"}


def card_class(ch):
    if ch in string.digits:
        return "D"
    return {" ": "SP", "-": "HY"}.get(ch, "O")


def _card_nfa():
    """Three branches guessed at the start: plain (a), spaces (b), hyphens (c).
    Each branch counts 16 digits; the grouped branches demand a separator after
    digits 4, 8 and 12 - the same separator throughout."""
    d = {}

    def arc(p, sym, q):
        d.setdefault((p, sym), set()).add(q)
    for branch, sep in (("a", None), ("b", "SP"), ("c", "HY")):
        arc("s", "D", f"{branch}1")
        for k in range(1, 16):
            if sep and k % 4 == 0:
                arc(f"{branch}{k}", sep, f"{branch}{k}s")
                arc(f"{branch}{k}s", "D", f"{branch}{k + 1}")
            else:
                arc(f"{branch}{k}", "D", f"{branch}{k + 1}")
    return NFA("Card number (NFA)", CARD_ALPHA, d, "s", {"a16", "b16", "c16"}, card_class)


CARD_NFA = _card_nfa()
CARD_SUBSET = CARD_NFA.subset_construction("Card number (subset DFA)")
CARD_DFA = CARD_SUBSET.minimise("Card number (minimal DFA)", prefix="c")

CARD_REGEX = r"\d{16}|\d{4}( \d{4}){3}|\d{4}(-\d{4}){3}"

# Luhn checksum over the raw digits (separators as above). For a 16-digit number
# the digits in positions 1, 3, ..., 15 (from the left) are doubled.
RAW_CARD_ALPHA = list(string.digits) + [" ", "-", "other"]


def raw_card_class(ch):
    return ch if ch in string.digits + " -" else "other"


def luhn_ok(digits):
    total = 0
    for i, ch in enumerate(digits):
        v = int(ch)
        if i % 2 == 0:                       # 16 digits: even index from the left is doubled
            v = v * 2 - 9 if v > 4 else v * 2
        total += v
    return total % 10 == 0


def _luhn_add(k, s, digit):
    """Add the (k+1)-th digit (k = digits already read) to the running sum mod 10."""
    v = int(digit)
    if k % 2 == 0:
        v = v * 2 - 9 if v > 4 else v * 2
    return (s + v) % 10


def _card_luhn():
    """State = (format, digits read, Luhn sum mod 10[, separator due]).
    Format x = still undecided (first four digits); the fifth character fixes it:
    a digit -> plain (a), a space -> spaced (b), a hyphen -> hyphenated (c)."""
    delta = {}
    for k in range(4):
        for s in range(10):
            for ch in string.digits:
                delta[(f"x:{k}:{s}", ch)] = f"x:{k + 1}:{_luhn_add(k, s, ch)}"
    for s in range(10):
        delta[("x:4:%d" % s, " ")] = f"b:4:{s}"
        delta[("x:4:%d" % s, "-")] = f"c:4:{s}"
        for ch in string.digits:
            delta[(f"x:4:{s}", ch)] = f"a:5:{_luhn_add(4, s, ch)}"
    for k in range(5, 16):
        for s in range(10):
            for ch in string.digits:
                delta[(f"a:{k}:{s}", ch)] = f"a:{k + 1}:{_luhn_add(k, s, ch)}"
    for fmt, sep in (("b", " "), ("c", "-")):
        for k in range(4, 16):
            for s in range(10):
                for ch in string.digits:
                    nk, ns = k + 1, _luhn_add(k, s, ch)
                    delta[(f"{fmt}:{k}:{s}", ch)] = f"{fmt}:{nk}:{ns}:due" if nk in (8, 12) \
                        else f"{fmt}:{nk}:{ns}"
                if k in (8, 12):
                    delta[(f"{fmt}:{k}:{s}:due", sep)] = f"{fmt}:{k}:{s}"
    raw = DFA("Card number + Luhn", RAW_CARD_ALPHA, delta, "x:0:0",
              {"a:16:0", "b:16:0", "c:16:0"}, raw_card_class)
    return raw.minimise("Card number + Luhn (minimal)", prefix="l")


CARD_LUHN_DFA = _card_luhn()


def card_reference(s, luhn):
    import re
    if not re.fullmatch(CARD_REGEX, s):
        return False
    return luhn_ok(s.replace(" ", "").replace("-", "")) if luhn else True


# ===========================================================================
# Registry
# ===========================================================================
APPLICATIONS = {
    "ip": {
        "title": "IPv4 address",
        "dfa": IP_EXACT_DFA,
        "accept": ["192.168.1.1", "10.0.0.255", "0.0.0.0", "255.255.255.255", "172.16.254.3",
                   "8.8.4.4"],
        "reject": ["256.1.1.1", "192.168.01.1", "192.168.1", "1.2.3.4.5", "192..1.1",
                   "1.2.3.", "a.b.c.d", "192.168.1.1 "],
    },
    "pan": {
        "title": "PAN card number",
        "dfa": PAN_DFA,
        "accept": ["ABCPE1234F", "AAACT5678K", "BNZPM2501F", "AAAHJ0001Z", "AABFG9999A",
                   "ZZZGX4321Q"],
        "reject": ["ABCDE1234F", "ABCPE1234", "abcpe1234f", "ABCP1234F", "ABCPE12345",
                   "ABCPE 1234F", "1BCPE1234F"],
    },
    "card": {
        "title": "Debit-card number + Luhn",
        "dfa": CARD_LUHN_DFA,
        "accept": ["4111111111111111", "4111 1111 1111 1111", "4111-1111-1111-1111",
                   "5500000000000004", "6070 0000 0000 0002", "4012888888881881"],
        "reject": ["4111111111111112", "4111 1111-1111 1111", "4111 11111111 1111",
                   "411111111111111", "4111  1111 1111 1111", "4111-1111-1111-111a",
                   "41111111111111111"],
    },
}

LIMITATIONS = {
    "ip": [
        "Whether the address is reachable, private or reserved (10.x, 127.x) is a policy "
        "decision made after the syntax check.",
        f"Exact octet ranges cost states: {IP_SHAPE_DFA.size()} for the shape, "
        f"{IP_EXACT_DFA.size()} for 0-255 without leading zeros.",
    ],
    "pan": [
        "The fifth letter is the initial of the holder's surname (or entity name): that "
        "needs the name, so it is a cross-field rule, not a language property.",
        "Whether the PAN exists or is linked to Aadhaar needs the income-tax database.",
    ],
    "card": [
        "Luhn is regular because it needs only the position and a sum mod 10, but it "
        f"raises the state count from {CARD_DFA.size()} to {CARD_LUHN_DFA.size()}.",
        "Expiry date, CVV, card status and the issuer's limits are semantic checks done "
        "by the bank, never by the form.",
    ],
}
