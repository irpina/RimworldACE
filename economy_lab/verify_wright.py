"""One command to check the Wright work is not fabricated.

    python -m economy_lab.verify_wright          # ~90 seconds
    python -m economy_lab.verify_wright --full   # adds the 200-run 2x2

Every check **recomputes** a number and compares it to what the document
claims, rather than printing a number for the reader to trust.  A FAIL
means a document is wrong, not that a run was unlucky: everything here
is seeded.

The checks are ordered by what they rule out:

1. **Structural** -- the model is a closed accounting system.  Money
   conservation and bit-identity cannot be produced by a process that
   is generating plausible-looking output.
2. **Instrument** -- the estimators recover known answers from synthetic
   data.  This validates the measurement stack *independently of the
   model*, so a reader need not trust the model to trust the fits.
3. **Documented** -- the headline figures in docs/112-120 reproduce.

What this cannot check is in ``docs/122``: whether the transcription is
Wright's model.  That needs a reader with the paper.
"""

import sys
import time

from economy_lab import distributions as D
from economy_lab import social_architecture as sa

WIDTH = 78
results = []


def check(name, claim, got, ok, where):
    results.append(ok)
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}")
    print(f"         {where} claims {claim}")
    print(f"         recomputed     {got}")


def section(title):
    print("\n" + title)
    print("-" * WIDTH)


def close(a, b, tol):
    return a is not None and abs(a - b) <= tol


def structural():
    section("1. STRUCTURAL -- properties a fabricated run could not have")

    worst = 0.0
    for seed in range(20):
        economy = sa.Economy(seed=seed)
        economy.run(180)
        worst = max(worst, abs(economy.total_coins() - 100_000.0))
    check("money is conserved over 20 seeds x 180 months",
          "< 1e-6", f"{worst:.2e}", worst < 1e-6, "docs/112")

    def state(economy):
        return (economy.money, economy.employer, economy.market,
                sorted(economy.firm_sizes()))

    same_one = same_zero = True
    for seed in (0, 1, 2):
        a = sa.Economy(seed=seed, market_rule="scaled", size_exponent=1.0)
        b = sa.Economy(seed=seed, market_rule="wright")
        c = sa.Economy(seed=seed, market_rule="scaled", size_exponent=0.0)
        d = sa.Economy(seed=seed, market_rule="neutral")
        for economy in (a, b, c, d):
            economy.run(90)
        same_one &= state(a) == state(b)
        same_zero &= state(c) == state(d)
    check("size_exponent=1.0 is bit-identical to Wright's rule",
          "identical", "identical" if same_one else "DIFFERS",
          same_one, "docs/119 P1")
    check("size_exponent=0.0 is bit-identical to the neutral ablation",
          "identical", "identical" if same_zero else "DIFFERS",
          same_zero, "docs/119 P1")

    first = sa.Economy(seed=11)
    second = sa.Economy(seed=11)
    first.run(120)
    second.run(120)
    check("the model is deterministic under a fixed seed",
          "identical", "identical" if first.money == second.money else "DIFFERS",
          first.money == second.money, "docs/111")


def instruments():
    section("2. INSTRUMENT -- estimators recover known answers")

    import random
    rng = random.Random(7)
    # Continuous power law with alpha_CSN = 2.5 by inverse transform.
    sample = [(1.0 - rng.random()) ** (-1.0 / 1.5) for _ in range(40000)]
    fit = D.power_law_fit(sample)
    got = fit["alpha"] if fit else None
    check("power_law_fit recovers a planted exponent (alpha_CSN = 2.5)",
          "2.50 +/- 0.05", f"{got:.3f}" if got else "no fit",
          close(got, 2.5, 0.05), "docs/113")

    check("the two exponent conventions differ by exactly one",
          "alpha_Wright = alpha_CSN - 1, so 2.0 -> 1.0 (Zipf)",
          f"{D.to_wright(2.0):.3f}", close(D.to_wright(2.0), 1.0, 1e-12),
          "docs/114")

    # Data drawn from a LOGNORMAL must not be reported as a power law.
    rng = random.Random(3)
    lognormal = [2.718281828 ** rng.gauss(0.0, 1.5) for _ in range(20000)]
    fit = D.power_law_fit(lognormal)
    ratio = D.likelihood_ratio(lognormal, fit["x_min"], fit["alpha"])
    value = ratio["normalised"] if ratio else None
    check("likelihood_ratio picks the lognormal on lognormal data",
          "negative and determined; this reported +9.09 before docs/113 "
          "fixed the untruncated fit",
          f"{value:.2f} ({ratio['favours']})" if ratio else "n/a",
          ratio is not None and value < -2.0
          and ratio["favours"] == "alternative", "docs/113")

    # Wright's fact 5 against the right null and the wrong one.
    rng = random.Random(5)
    geometric = []
    while len(geometric) < 600:
        n, p = 1, 0.55
        while rng.random() > p:
            n += 1
        geometric.append(n)
    right = D.geometric_goodness_of_fit(geometric, synthetics=200, seed=1)
    wrong = D.exponential_goodness_of_fit(geometric, synthetics=200, seed=1)
    ok = bool(right and wrong and right["ks"] < wrong["ks"] / 3)
    check("integer durations fit a geometric null, not a continuous one",
          "KS(geometric) far below KS(exponential) -- the wrong null is "
          "what made Wright's fact 5 look refuted",
          f"{right['ks']:.4f} vs {wrong['ks']:.4f}" if right and wrong else "n/a",
          ok, "docs/113")


def documented(full):
    section("3. DOCUMENTED -- headline figures reproduce")

    economy = sa.Economy(seed=0)
    economy.run(120)
    economy.start_recording()
    economy.run(180)
    history = economy.history

    fit = D.power_law_fit(history.firm_sizes, discrete=True, min_tail=200)
    alpha = fit["alpha_wright"] if fit else None
    check("firm-size exponent at Wright's own rule, seed 0",
          "~1.2-1.3 per seed at n~21,900 (NOT his 1.038 -- docs/120 s4)",
          f"{alpha:.3f} at n={len(history.firm_sizes)}" if alpha else "no fit",
          close(alpha, 1.25, 0.25), "docs/119")

    kurtosis = D.excess_kurtosis(history.firm_growth)
    check("firm-growth excess kurtosis at Wright's rule",
          "~3.9 (Laplace = 3), and rising above beta=1",
          f"{kurtosis:.3f}", close(kurtosis, 3.9, 1.2), "docs/120 s2")

    # The claim docs/120 rests on: growth kurtosis binds from ABOVE.
    above = sa.Economy(seed=0, market_rule="scaled", size_exponent=1.05)
    above.run(120)
    above.start_recording()
    above.run(180)
    higher = D.excess_kurtosis(above.history.firm_growth)
    check("raising the exponent to 1.05 makes growth FATTER, not better",
          "kurtosis rises well past Laplace's 3",
          f"{kurtosis:.2f} at beta=1.00 -> {higher:.2f} at beta=1.05",
          higher > kurtosis + 1.0, "docs/120 s2")

    # The saturation mechanism, counted from outside the model.
    for beta, expected in ((1.0, 0.0), (5.0, 0.9)):
        economy = sa.Economy(seed=0, market_rule="scaled", size_exponent=beta)
        original, stats = economy._sample, {"calls": 0, "capped": 0}

        def probe(a, _economy=economy, _original=original, _stats=stats):
            before = _economy.market
            _original(a)
            if before > 0.0 and not _economy.is_unemployed(a):
                _stats["calls"] += 1
                _stats["capped"] += _economy.market == 0.0

        economy._sample = probe
        economy.run(150)
        fraction = stats["capped"] / stats["calls"] if stats["calls"] else 0.0
        check(f"draws hitting the pool cap at beta={beta}",
              "0% at beta=1, ~99% at beta=5 -- the model cannot exceed beta=1",
              f"{fraction:.1%}",
              fraction <= 0.001 if beta == 1.0 else fraction >= expected,
              "docs/119 s5")

    if not full:
        print("\n  (--full adds the 200-run docs/116 2x2, about 3 minutes)")
        return

    from economy_lab import m1_ablation as ablation
    runs = ablation.sweep(seeds=50)
    rows = {rule: ablation.pooled(runs, rule) for rule in sa.ABLATION_RULES}
    check("docs/116: removing the size bias destroys the firm-size tail",
          "alpha 1.337 (wright) -> 4.715 (neutral), pooled over 50 seeds",
          f"{rows['wright']['alpha']:.3f} -> {rows['neutral']['alpha']:.3f}",
          close(rows["wright"]["alpha"], 1.337, 0.02)
          and close(rows["neutral"]["alpha"], 4.715, 0.02), "docs/116")
    means = {rule: st for rule, st in
             ((r, ablation.per_seed(runs, r, "growth_kurtosis")) for r in sa.ABLATION_RULES)}
    import statistics
    cell = {rule: statistics.mean(values) for rule, values in means.items()}
    effects = ablation.decompose(cell)
    check("docs/116: linearity carries Laplace growth, not contingency",
          "main effect +2.52 for linearity vs -0.43 for contingency",
          f"{effects['main_l']:+.2f} vs {effects['main_r']:+.2f}",
          close(effects["main_l"], 2.52, 0.05)
          and close(effects["main_r"], -0.43, 0.05), "docs/116")


def main(argv):
    full = "--full" in argv
    started = time.time()
    print("=" * WIDTH)
    print("VERIFYING THE WRIGHT WORK (docs/111-121)".center(WIDTH))
    print("=" * WIDTH)
    print("\nNo third-party dependencies. Everything below is recomputed now")
    print("and compared against the figure the cited document claims.")

    structural()
    instruments()
    documented(full)

    section("RESULT")
    passed = sum(1 for ok in results if ok)
    print(f"  {passed}/{len(results)} checks passed in {time.time()-started:.0f}s")
    if passed != len(results):
        print("\n  A FAIL means a DOCUMENT IS WRONG. Please report it.")
    print("\n  What this does NOT check: whether the transcription in")
    print("  economy_lab/social_architecture.py is Wright's model. That is")
    print("  584 lines, and only a reader with the paper can judge it.")
    print("  See docs/122 for the rest of the audit trail.\n")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
