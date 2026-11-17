"""Rebuild docs/diagrams/*, docs/automata.json and the browser demo docs/index.html.
Needs Graphviz (`dot`) on PATH."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fa_checks.validators import (APPLICATIONS, CARD_DFA, CARD_EDGE, CARD_NFA,  # noqa: E402
                                  IP_EXACT_DFA, IP_SHAPE_DFA, PAN_DFA)

OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

DIAGRAMS = {
    "ip_shape_dfa": IP_SHAPE_DFA.to_dot(edge_names={"DOT": "."}),
    "ip_exact_dfa": IP_EXACT_DFA.to_dot(),
    "pan_dfa": PAN_DFA.to_dot(),
    "card_nfa": CARD_NFA.to_dot(edge_names=CARD_EDGE),
    "card_dfa": CARD_DFA.to_dot(edge_names=CARD_EDGE),
}

for name, dot in DIAGRAMS.items():
    (OUT / f"{name}.dot").write_text(dot, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", "-o", str(OUT / f"{name}.svg")], input=dot.encode(), check=True)
    subprocess.run(["dot", "-Gdpi=170", "-Tpng", "-o", str(OUT / f"{name}.png")],
                   input=dot.encode(), check=True)
    print("wrote", name)

export = {}
for key, app in APPLICATIONS.items():
    d = app["dfa"]
    export[key] = {"title": app["title"], "name": d.name, "start": d.start,
                   "accepting": sorted(d.accepting), "alphabet": d.alphabet,
                   "delta": {f"{p}|{a}": q for (p, a), q in d.delta.items()},
                   "examples": {"accept": app["accept"], "reject": app["reject"]},
                   "states": d.size()}
(ROOT / "docs" / "automata.json").write_text(json.dumps(export, indent=1), encoding="utf-8")
print("wrote docs/automata.json")

svgs = {}
for key, fname in {"ip": "ip_exact_dfa", "pan": "pan_dfa"}.items():
    text = (OUT / f"{fname}.svg").read_text(encoding="utf-8")
    svgs[key] = text[text.index("<svg"):]
page = (ROOT / "tools" / "demo_template.html").read_text(encoding="utf-8")
page = page.replace("__JSON__", json.dumps(export)).replace("__SVG__", json.dumps(svgs))
(ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")
print("wrote docs/index.html")
