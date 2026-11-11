"""Weekly label-distribution drift report using Jensen-Shannon divergence."""
import json
import math
import sys
from collections import Counter
from pathlib import Path


def js_divergence(a, b):
    keys = set(a) | set(b)
    pa = {k: a.get(k, 0) / max(1, sum(a.values())) for k in keys}
    pb = {k: b.get(k, 0) / max(1, sum(b.values())) for k in keys}
    m = {k: (pa[k] + pb[k]) / 2 for k in keys}
    def kl(p): return sum(v * math.log2(v / m[k]) for k, v in p.items() if v > 0)
    return (kl(pa) + kl(pb)) / 2


baseline, incoming = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])
a, b = Counter(baseline), Counter(incoming)
print(json.dumps({"baseline": a, "incoming": b, "js_divergence": js_divergence(a, b),
                  "alert": js_divergence(a, b) >= 0.1}, indent=2))
