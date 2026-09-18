using System;
using System.Collections.Generic;
using System.Globalization;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// How many phases fit in a frame, from measured phase durations
    /// (docs/88 section 3).
    ///
    /// `PhasesPerTick` is 1 today because a guess was needed (docs/83
    /// section 5). The honest way to set it is to time each phase in the
    /// game and choose the count that fits a frame budget — and that
    /// arithmetic is not game-specific, so it lives here where it can be
    /// tested, and the game supplies only the stopwatch.
    /// </summary>
    public static class TickBudget
    {
        /// <summary>
        /// A conservative slice of a 60 Hz frame (16.7 ms) for the
        /// economy: enough to make progress, small enough that the rest
        /// of the game does not notice.
        /// </summary>
        public const double DefaultBudgetMs = 2.0;

        /// <summary>
        /// The number of phases to run per tick, given what each phase
        /// cost last time.
        ///
        /// Never less than 1: a scheduler that runs zero phases a tick
        /// never finishes a day. Never more than the number of phases
        /// there are. Degrades to 1 on nonsense — an empty timing set, a
        /// non-finite duration, a budget of zero — because a wrong
        /// recommendation must be the safe one.
        /// </summary>
        public static int Recommend(IList<double> phaseMillis, double budgetMs)
        {
            if (phaseMillis == null || phaseMillis.Count == 0)
            {
                return 1;
            }
            if (double.IsNaN(budgetMs) || double.IsInfinity(budgetMs) || budgetMs <= 0.0)
            {
                return 1;
            }
            double spent = 0.0;
            int fitted = 0;
            for (int i = 0; i < phaseMillis.Count; i++)
            {
                double cost = phaseMillis[i];
                if (double.IsNaN(cost) || double.IsInfinity(cost) || cost < 0.0)
                {
                    break;
                }
                if (spent + cost > budgetMs)
                {
                    break;
                }
                spent += cost;
                fitted++;
            }
            if (fitted < 1)
            {
                return 1;
            }
            return fitted > phaseMillis.Count ? phaseMillis.Count : fitted;
        }

        /// <summary>
        /// True when no single phase fits the budget, so the budget cannot
        /// be met however the day is sliced: a phase is atomic (docs/82
        /// section 2) and no scheduler can split one.
        /// </summary>
        public static bool BudgetUnreachable(IList<double> phaseMillis, double budgetMs)
        {
            if (phaseMillis == null || phaseMillis.Count == 0)
            {
                return false;
            }
            foreach (double cost in phaseMillis)
            {
                if (double.IsNaN(cost) || double.IsInfinity(cost))
                {
                    continue;
                }
                if (cost <= budgetMs)
                {
                    return false;
                }
            }
            return true;
        }

        /// <summary>A line for the self-check report.</summary>
        public static string Describe(IList<double> phaseMillis, double budgetMs)
        {
            int recommended = Recommend(phaseMillis, budgetMs);
            double total = 0.0;
            double worst = 0.0;
            if (phaseMillis != null)
            {
                foreach (double cost in phaseMillis)
                {
                    if (double.IsNaN(cost) || double.IsInfinity(cost) || cost < 0.0) continue;
                    total += cost;
                    if (cost > worst) worst = cost;
                }
            }
            string text = "recommend PhasesPerTick=" + recommended.ToString(CultureInfo.InvariantCulture)
                + " for a " + budgetMs.ToString("0.##", CultureInfo.InvariantCulture) + " ms budget"
                + "; day total " + total.ToString("0.###", CultureInfo.InvariantCulture) + " ms"
                + ", worst phase " + worst.ToString("0.###", CultureInfo.InvariantCulture) + " ms";
            if (BudgetUnreachable(phaseMillis, budgetMs))
            {
                text += "; NO SINGLE PHASE FITS -- a phase is atomic and cannot be split";
            }
            return text;
        }
    }
}
