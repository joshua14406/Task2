"""
Command-line demo for the Task 2 validators.

  python -m fa_checks.cli                        accept/reject table for every application
  python -m fa_checks.cli ip 192.168.01.1     one string with its full transition trace
  python -m fa_checks.cli --stats                state counts of every design
  python -m fa_checks.cli --limits               what each automaton cannot check
"""
import sys

from .automata import TRAP
from .validators import (APPLICATIONS, CARD_DFA, CARD_LUHN_DFA, CARD_NFA, CARD_SUBSET,
                         IP_EXACT_DFA, IP_SHAPE_DFA, LIMITATIONS, PAN_DFA, PAN_SHAPE_DFA)

COLOUR = sys.stdout.isatty() or "--color" in sys.argv
GREEN, RED, BOLD, DIM, END = ("\033[32m", "\033[31m", "\033[1m", "\033[2m", "\033[0m") \
    if COLOUR else ("",) * 5


def shown(s):
    return "ε" if s == "" else (repr(s) if " " in s else s)


def verdict(ok):
    return f"{GREEN}ACCEPT{END}" if ok else f"{RED}REJECT{END}"


def table(key):
    app = APPLICATIONS[key]
    dfa = app["dfa"]
    print(f"\n{BOLD}{app['title']}{END}  {DIM}[{dfa.name}, {dfa.size()} states incl. trap]{END}")
    print(f"  {'input':<32}{'expected':<10}{'result':<8}  final state")
    rows = [(s, True) for s in app["accept"]] + [(s, False) for s in app["reject"]]
    good = 0
    for s, expected in rows:
        ok, steps = dfa.run(s)
        final = steps[-1][3] if steps else dfa.start
        good += ok == expected
        flag = "" if ok == expected else "   <-- MISMATCH"
        print(f"  {shown(s):<32}{('ACCEPT' if expected else 'REJECT'):<10}{verdict(ok)}  {final}{flag}")
    print(f"  {DIM}{good}/{len(rows)} as expected{END}")
    return good == len(rows)


def trace(key, text):
    dfa = APPLICATIONS[key]["dfa"]
    ok, steps = dfa.run(text)
    print(f"{BOLD}{dfa.name}{END} on '{text}'")
    for i, (p, ch, sym, q) in enumerate(steps, 1):
        note = "   (trap: can never accept)" if q == TRAP and p != TRAP else ""
        print(f"  {i:>2}. δ({p}, '{ch}' -> {sym}) = {q}{note}")
    final = steps[-1][3] if steps else dfa.start
    print(f"  final state {final} -> {'ACCEPTED' if ok else 'REJECTED'}")


def stats():
    print(f"{BOLD}Design comparison (reachable states, trap included){END}")
    rows = [
        ("IPv4: shape (1-3 digits per part), Σ = {D, ., O}", IP_SHAPE_DFA.size()),
        ("IPv4: exact octets 0-255, no leading zeros (minimal)", IP_EXACT_DFA.size()),
        ("PAN: shape only, Σ = {H, L, D, O}", PAN_SHAPE_DFA.size()),
        ("PAN: with holder-type rule (4th letter)", PAN_DFA.size()),
        ("Card: hand-written NFA (3 guessed formats)", len(CARD_NFA.states)),
        ("Card: subset-construction DFA", CARD_SUBSET.size()),
        ("Card: minimal DFA", CARD_DFA.size()),
        ("Card: format + Luhn checksum (minimal)", CARD_LUHN_DFA.size()),
    ]
    for name, n in rows:
        print(f"  {name:<62}{n:>5}")
    print(f"\n{BOLD}Minimal card DFA: NFA subsets merged into each state{END}")
    for m, members in CARD_DFA.members.items():
        print(f"  {m:<6}{', '.join(members)}")


def limits():
    for key, items in LIMITATIONS.items():
        print(f"\n{BOLD}Limitations - {APPLICATIONS[key]['title']}{END}")
        for item in items:
            print(f"  - {item}")


def main(argv):
    args = [a for a in argv if a != "--color"]
    if not args:
        ok = all([table(k) for k in APPLICATIONS])
        print(f"\n{BOLD}All listed examples behaved as expected: {ok}{END}")
        return 0 if ok else 1
    if args[0] == "--stats":
        stats()
        return 0
    if args[0] == "--limits":
        limits()
        return 0
    if args[0] in APPLICATIONS and len(args) >= 2:
        trace(args[0], " ".join(args[1:]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
