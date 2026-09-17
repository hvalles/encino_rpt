"""Smoke test de rendimiento: entrada grande (50k filas) y wall-clock acotado.

Gate pass/fail con `time.perf_counter()` (sin `pytest-benchmark` ni markers).
"""

import time

from encino_rpt import Report


def test_pivot_50k_rows_smoke():
    n = 50_000
    rows = [
        {"region": f"r{i % 50}", "product": f"p{i % 200}", "amount": i % 100}
        for i in range(n)
    ]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").pivot("region", "product", operator="sum", value_column="amount")

    t0 = time.perf_counter()
    result = rep.run()
    elapsed = time.perf_counter() - t0

    pivot = result.root.children[-1]
    assert len(pivot.rows) == 50
    assert len(pivot.columns) == 200
    assert pivot.row_totals[0] == sum(i % 100 for i in range(n) if i % 50 == 0)
    assert elapsed < 10.0, f"pivot 50k tardó {elapsed:.2f}s (límite 10s)"
