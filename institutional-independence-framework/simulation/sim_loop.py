#!/usr/bin/env python3
"""
Longitudinal simulation of the institutional confirmation loop.

CLAIM BEING TESTED:
  Institutional selection alone -- with NO change to the advisor's underlying
  decision function -- causes recommendation diversity to contract over time
  (governance drift). We show drift appears under selection and is absent
  without it, and that its magnitude scales with selection strength.

DESIGN (deliberately transparent):
  - An advisor maps each case to a recommendation DISTRIBUTION over
    {APPROVE, FLAG, REJECT}. This distribution is FIXED -- the advisor never
    "learns." It depends only on the case's true risk.
  - Each turn: a case arrives; the advisor samples a recommendation; the
    institution decides whether to RETAIN that recommendation in the working
    context (reuse / escalate) based on whether it matches the institution's
    incentive (e.g. APPROVE-preferring).
  - The retained context biases WHICH CASES the institution brings forward
    next (it surfaces more cases where the advisor's output was incentive-
    aligned) -- modeling workflow selection, not model retraining.
  - We measure recommendation entropy H(R) over a sliding window across turns.

  Drift = decline in H(R). The advisor's risk function is identical in all
  conditions; only the institution's selection behavior changes.
"""
import numpy as np
import json

RNG = np.random.default_rng(42)
RECS = ["APPROVE", "FLAG", "REJECT"]
N_TURNS = 200
WINDOW = 30
N_RUNS = 50  # average over runs to smooth sampling noise


def advisor_distribution(true_risk):
    """
    FIXED advisor: maps a case's true risk in [0,1] to a recommendation
    distribution. Low risk -> APPROVE-leaning; high risk -> REJECT-leaning;
    mid risk -> FLAG-leaning. This never changes across turns or conditions.
    """
    # logits centered so that risk ~0 -> approve, ~0.5 -> flag, ~1 -> reject
    approve = np.exp(-((true_risk - 0.0) ** 2) / (2 * 0.18 ** 2))
    flag    = np.exp(-((true_risk - 0.5) ** 2) / (2 * 0.18 ** 2))
    reject  = np.exp(-((true_risk - 1.0) ** 2) / (2 * 0.18 ** 2))
    p = np.array([approve, flag, reject])
    return p / p.sum()


def entropy(counts):
    p = counts / counts.sum() if counts.sum() > 0 else np.ones(3) / 3
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def run_one(selection_strength):
    """
    selection_strength in [0,1]:
      0   -> institution does NOT select (cases drawn neutrally)  [CONTROL]
      >0  -> institution increasingly surfaces cases whose advised
             recommendation matches its incentive (APPROVE)
    Returns list of windowed H(R) across turns (after warmup).
    """
    incentive = "APPROVE"  # institution rewarded for approvals
    # Latent cases span the full risk range. Selection reshapes which risks recur.
    risk_pool = RNG.uniform(0, 1, size=2000)
    weights = np.ones_like(risk_pool)

    recent = []
    h_series = []

    # Warm up the window so entropy starts from a full, representative window
    # (avoids the artifact of entropy rising simply because the window fills).
    total_turns = N_TURNS + WINDOW

    for t in range(total_turns):
        probs = weights / weights.sum()
        idx = RNG.choice(len(risk_pool), p=probs)
        risk = risk_pool[idx]

        dist = advisor_distribution(risk)   # FIXED advisor
        rec = RNG.choice(RECS, p=dist)

        recent.append(rec)
        if len(recent) > WINDOW:
            recent.pop(0)

        # Institution selection: when the advised recommendation matches the
        # incentive, up-weight the LOW-RISK region (where the advisor reliably
        # produces APPROVE). Over time the working set concentrates on low-risk
        # cases, so the advisor's *recommendations* collapse toward APPROVE --
        # not because the advisor changed, but because the institution stopped
        # bringing it the cases that would have produced FLAG/REJECT.
        if selection_strength > 0 and rec == incentive:
            kernel = np.exp(-((risk_pool - 0.0) ** 2) / (2 * 0.25 ** 2))
            weights += selection_strength * kernel

        if t >= WINDOW:  # record only after warmup
            counts = np.array([recent.count(r) for r in RECS], dtype=float)
            h_series.append(entropy(counts))

    return h_series


def average_runs(selection_strength):
    series = np.zeros(N_TURNS)
    for _ in range(N_RUNS):
        series += np.array(run_one(selection_strength))
    return series / N_RUNS


def main():
    conditions = {
        "no_selection (control)": 0.0,
        "weak_selection": 0.15,
        "moderate_selection": 0.4,
        "strong_selection": 1.0,
    }
    results = {}
    for name, s in conditions.items():
        h = average_runs(s)
        results[name] = h
        print(f"{name:28} H(R) start={h[:10].mean():.3f}  end={h[-10:].mean():.3f}  "
              f"drop={h[:10].mean()-h[-10:].mean():+.3f}")

    # save series
    out = {k: v.tolist() for k, v in results.items()}
    with open("sim_results.json", "w") as f:
        json.dump(out, f)
    print("\nSaved sim_results.json")
    return results


if __name__ == "__main__":
    main()
