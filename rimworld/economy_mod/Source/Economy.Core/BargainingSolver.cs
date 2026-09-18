using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// The two magnitudes the bargaining rules carry from day to day.
    ///
    /// These are the model's only stateful accumulators outside the
    /// ledger (docs/74 section 2): both are moved by <c>+=</c>, so an
    /// error of one ulp on the first day is compounded by every day
    /// after it, and the fixtures are sequences rather than single
    /// applications for that reason.
    /// </summary>
    public sealed class BargainingState
    {
        public string Name;
        /// <summary>False for a region with no subsistence basket: both rules return.</summary>
        public bool HasBasket = true;
        public double EmploymentRate;
        public double ReferenceEmploymentRate;
        public double WagePremium;
        public double HabitualScale = 1.0;
    }

    /// <summary>What the two rules read that does not change day to day.</summary>
    public sealed class BargainingProblem
    {
        public double WageBargainingStrength;
        public double WageBargainingSpeed;
        public double HabituationSpeed;
        public List<BargainingState> Regions = new List<BargainingState>();
    }

    /// <summary>
    /// The reserve-army premium (docs/46) and habituation (docs/51),
    /// ported to the bit from <c>Economy._bargain</c> and
    /// <c>Economy._habituate</c> (docs/74).
    ///
    /// Three things are transliteration rather than translation, and each
    /// is a place the port could be merely correct instead of identical
    /// (docs/74 section 3):
    ///
    /// * both methods **return before touching anything** when their
    ///   parameter is zero.  Multiplying by a zero strength instead would
    ///   agree on every fixture and diverge the first time a scenario
    ///   paired a negative premium with a zero speed, because
    ///   <c>-0.0 + 0.0 * y</c> is not <c>-0.0</c>;
    /// * the compound assignment is one rounding of the product, one of
    ///   the difference and one of the sum, in that order.  The
    ///   algebraically identical <c>p * (1 - s) + s * t</c> rounds three
    ///   different times and would be wrong;
    /// * the ratchet compares <c>gap &gt; 0.0</c>, and a negative zero gap
    ///   is correctly not greater.  Safe in both languages, written down
    ///   so the next reader need not re-derive it.
    /// </summary>
    public static class BargainingSolver
    {
        /// <summary>
        /// Move the wage premium toward what the reserve army allows.
        ///
        /// The target is proportional to how far yesterday's employment
        /// sits from the seeded reference, and the premium closes a fixed
        /// fraction of the gap each day.  At the seeded equilibrium the
        /// rate equals the reference to the bit, so the target is exactly
        /// zero and the premium never leaves it: the rule is exactly
        /// stationary where the circuit is.
        /// </summary>
        public static void Bargain(BargainingProblem problem, BargainingState region)
        {
            if (problem.WageBargainingStrength == 0.0 || !region.HasBasket)
            {
                return;
            }
            double target = problem.WageBargainingStrength
                * (region.EmploymentRate - region.ReferenceEmploymentRate);
            region.WagePremium += problem.WageBargainingSpeed
                * (target - region.WagePremium);
        }

        /// <summary>
        /// Let a sustained premium become the habitual standard.
        ///
        /// The standard closes a fixed fraction of the gap to the paid
        /// real wage each day, and only upward: a standard that has risen
        /// does not fall when the premium goes, so a wage that falls back
        /// afterwards is a wage below the value of labor-power, reported
        /// and not prevented.
        /// </summary>
        public static void Habituate(BargainingProblem problem, BargainingState region)
        {
            if (problem.HabituationSpeed == 0.0 || !region.HasBasket)
            {
                return;
            }
            double gap = (1.0 + region.WagePremium) - region.HabitualScale;
            if (gap > 0.0)
            {
                region.HabitualScale += problem.HabituationSpeed * gap;
            }
        }

        /// <summary>
        /// One day of both rules, in the model's order: bargaining moves
        /// the premium, and habituation then reads the premium bargaining
        /// has just set.
        /// </summary>
        public static void Step(BargainingProblem problem, BargainingState region)
        {
            Bargain(problem, region);
            Habituate(problem, region);
        }
    }
}
