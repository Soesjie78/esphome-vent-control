"""Minimal S-expression parser/writer for KiCad files."""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:\\.|[^"\\])*")|([^\s()"]+))')


class Sym(str):
    """Unquoted atom."""


def parse(text):
    pos = 0
    stack = [[]]
    while True:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        lp, rp, s, a = m.groups()
        if lp:
            stack.append([])
        elif rp:
            node = stack.pop()
            stack[-1].append(node)
        elif s is not None:
            stack[-1].append(s[1:-1].replace('\\"', '"').replace('\\\\', '\\'))
        else:
            stack[-1].append(Sym(a))
    return stack[0][0]


def find(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def find_all(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def fmt_atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, (int, float)):
        return num(a)
    return '"' + str(a).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def num(v):
    if isinstance(v, int):
        return str(v)
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return "0" if s in ("-0", "") else s


def dump(node, indent=0):
    if not isinstance(node, list):
        return fmt_atom(node)
    simple = all(not isinstance(c, list) for c in node)
    if simple or len(str(node)) < 70 and sum(isinstance(c, list) for c in node) <= 1 and not any(
            isinstance(c, list) and any(isinstance(cc, list) for cc in c) for c in node):
        return "(" + " ".join(dump(c) for c in node) + ")"
    # order preserving: lists go on their own line, atoms stay inline
    out = "("
    first = True
    for c in node:
        if isinstance(c, list):
            out += "\n" + "  " * (indent + 1) + dump(c, indent + 1)
        else:
            out += ("" if first else " ") + dump(c)
        first = False
    return out + "\n" + "  " * indent + ")"
