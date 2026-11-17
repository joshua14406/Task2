# Finite-Automaton Field Checks: IPv4, PAN and Card Numbers

**Course:** 21CSC301T Formal Language and Automata, CLA-2, Assessment Task 2
**Student:** Joshua Pope (RA2411026050273), jp2155@srmist.edu.in
**Faculty:** Dr. C. Gunasundari, Assistant Professor, Department of AIML, SRM IST Tiruchirappalli

| # | Field | Automaton | States (incl. trap) |
|---|---|---|---|
| 1 | IPv4 address (192.168.1.1) | shape DFA → exact-octet DFA (0–255, no leading zeros) | 17 → 25 |
| 2 | PAN card number (ABCPE1234F) | DFA over classes {H, L, D, O}; holder-type rule costs nothing | 12 → 12 |
| 3 | Debit-card number (4111 1111 1111 1111) | NFA guessing the grouping style → subset DFA → minimal DFA → + Luhn checksum | 55 → 48 → 38 → 353 |

All counts are printed by `python -m fa_checks.cli --stats`; every automaton is tested
against an independent regex or arithmetic rule.

## Run it

```bash
pip install pytest
python -m fa_checks.cli                       # accept/reject table for every field
python -m fa_checks.cli ip 192.168.01.1       # one string with its δ-trace
python -m fa_checks.cli --stats               # state counts and NFA subsets
python -m fa_checks.cli --limits              # what each automaton cannot check
python -m pytest -q                           # 15 checks
python tools/make_diagrams.py                 # rebuild diagrams + browser demo (Graphviz)
```

Open `docs/index.html` for the browser demo (current state highlighted as you type).

## 1. IPv4 address

The **shape** (four parts of 1–3 digits joined by dots) needs 16 states plus a trap over
Σ = {D, ., O}. The **exact** rule (each part 0–255, no leading zeros such as `01`) needs the
raw digits. Built as a trie of the 256 valid octets and minimised, it collapses to **6 states
per part**: just started, "a 1 was read" (two more digits allowed), "a 2 was read" (next
digit decides), "25 was read" (last digit 0–5), "one more digit allowed", and "complete" —
24 states plus the trap.

![IPv4 exact DFA](docs/diagrams/ip_exact_dfa.png)

## 2. PAN card number

AAAAA9999A, where the 4th letter is the holder type (P person, C company, H HUF, F firm,
A AOP, T trust, B BOI, L local authority, J artificial juridical person, G government).
Choosing the classes H (holder-type letters) and L (other letters) makes the holder rule
**free**: the DFA has 12 states with or without it. The 5th letter must equal the initial of
the holder's surname — a cross-field rule that needs the name, so no automaton over the
PAN alone can check it.

![PAN DFA](docs/diagrams/pan_dfa.png)

## 3. Debit-card number and the Luhn checksum

16 digits, written plain, in groups of four with spaces, or with hyphens — but never mixed.
The NFA guesses the style at the first digit (branches a, b, c):

![card NFA](docs/diagrams/card_nfa.png)

Subset construction gives 47 live states; minimisation (38 incl. trap) merges the three
branches again in the last group, because after the third separator every style needs
exactly "four more digits":

![card DFA](docs/diagrams/card_dfa.png)

The **Luhn checksum** (every second digit from the left doubled, total ≡ 0 mod 10) is
regular too — the DFA only needs the position and the running sum mod 10 — but it costs
**353** states. Tests confirm it catches every single-digit error.

## Tests (15)

All 349 525 strings up to length 9 over {1, 0, ., x} for the IPv4 shape; all 1 110 one-to-three
digit parts in all four positions plus 60 000 random strings for the exact DFA; 80 000 PAN
candidates against a regex; all 27 separator combinations and 60 000 random card strings;
40 000 random card numbers against a plain Luhn function; exact equivalence of the subset
and minimal card DFAs.

## What a finite automaton cannot do here

* Reachability or ownership of an IP address, existence of a PAN, card status, expiry and
  CVV need outside systems.
* The PAN's 5th letter depends on another field (the surname).
* Value rules are regular but have a price: 17 → 25 (IPv4), 38 → 353 (Luhn). A short
  function next to the DFA is usually the better engineering choice.

## Layout

```
fa_checks/automata.py     DFA, NFA, subset construction, product, minimisation, DOT export
fa_checks/validators.py   the three fields, test strings and limitations
fa_checks/cli.py          terminal demo
tests/test_validators.py  15 checks
tools/                    diagram + demo generator
docs/                     diagrams and the browser demo
```
