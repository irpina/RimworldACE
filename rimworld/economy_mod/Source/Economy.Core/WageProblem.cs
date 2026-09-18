using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// One region as the wage relation reads it (docs/72).
    ///
    /// The basket, the prices and the two bargaining magnitudes are
    /// regional; the labor values the basket is valued at are not, and live
    /// on <see cref="WageProblem"/>.  A port that read social values
    /// regionally would pass a one-region fixture and be wrong.
    /// </summary>
    public sealed class RegionState
    {
        public string Name;
        /// <summary>Quantity of each good per worker-day, in the model's order.</summary>
        public List<Quantity> SubsistenceBasket = new List<Quantity>();
        public List<Quantity> Prices = new List<Quantity>();
        /// <summary>What bargaining has won above the basket (docs/46); zero when off.</summary>
        public double WagePremium;
        /// <summary>The habitual standard (docs/51); exactly one when it has not moved.</summary>
        public double HabitualScale = 1.0;
        /// <summary>
        /// The labor pool, or null for an unbounded reserve army -- the
        /// laboratory's <c>float("inf")</c>, which JSON cannot carry.
        /// </summary>
        public double? LaborPool;
        public double WorkerDaysEarned;
        public double TicksPerWorkerDay;
        public double Cash;
        public double WorkerCash;

        public double PriceOf(string commodity)
        {
            for (int i = 0; i < Prices.Count; i++)
            {
                if (Prices[i].Name == commodity)
                {
                    return Prices[i].Amount;
                }
            }
            return 0.0;
        }
    }

    /// <summary>The day's labor for one producer, as production accumulated it.</summary>
    public struct LaborEntry
    {
        public readonly string Producer;
        public readonly double Ticks;

        public LaborEntry(string producer, double ticks)
        {
            Producer = producer;
            Ticks = ticks;
        }
    }

    /// <summary>The wage's inputs: the regions, and the social values they read.</summary>
    public sealed class WageProblem
    {
        /// <summary>
        /// The binary grid employment is quantized to, 2^-20 by default.
        /// Zero means no quantization, which the laboratory also allows.
        /// </summary>
        public double EmploymentQuantum;
        /// <summary>Which names are commodities: the basket may name others.</summary>
        public List<string> Commodities = new List<string>();
        public List<Quantity> LaborValues = new List<Quantity>();
        public List<RegionState> Regions = new List<RegionState>();

        public double LaborValueOf(string commodity)
        {
            for (int i = 0; i < LaborValues.Count; i++)
            {
                if (LaborValues[i].Name == commodity)
                {
                    return LaborValues[i].Amount;
                }
            }
            return 0.0;
        }

        public bool IsCommodity(string name)
        {
            for (int i = 0; i < Commodities.Count; i++)
            {
                if (Commodities[i] == name)
                {
                    return true;
                }
            }
            return false;
        }
    }

    /// <summary>
    /// The running totals a settlement posts onto, and what they are
    /// afterwards (docs/72 section 4).
    ///
    /// Absolute and not a difference, deliberately.  The laboratory's
    /// <c>Ledger.add</c> accumulates onto a running total and the two
    /// purses are subtracted from and added to, so the same wage bill
    /// lands on a different last bit against a larger base.  A port
    /// checked on differences would agree while disagreeing with the
    /// model.
    /// </summary>
    public sealed class LedgerTotals
    {
        public double WagesPaid;
        public double LivingLabor;
        public double NecessaryLabor;
        public double WagePremiumPaid;
        public double WageDeviationLabor;
        public double Cash;
        public double WorkerCash;

        public LedgerTotals Copy()
        {
            return new LedgerTotals
            {
                WagesPaid = WagesPaid,
                LivingLabor = LivingLabor,
                NecessaryLabor = NecessaryLabor,
                WagePremiumPaid = WagePremiumPaid,
                WageDeviationLabor = WageDeviationLabor,
                Cash = Cash,
                WorkerCash = WorkerCash,
            };
        }
    }

    /// <summary>A day's wage relation: the employment it set and the totals it left.</summary>
    public sealed class Settlement
    {
        public double WorkerDaysEarned;
        public LedgerTotals After;
    }
}
