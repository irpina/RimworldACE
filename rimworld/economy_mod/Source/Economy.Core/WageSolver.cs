using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// The basket and the wage (docs/17, docs/46, docs/51), ported to the
    /// bit from <c>Region.basket_cost</c>, <c>Region.wage_rate</c>,
    /// <c>Economy.basket_labor_value</c>,
    /// <c>Economy.value_of_labor_power</c>, <c>Region.employment_rate</c>,
    /// <c>Region.premium_over_value</c> and <c>Economy._settle_labor</c>
    /// (docs/72).
    ///
    /// Three things here are transliteration rather than translation, and
    /// each is a place the port could be merely correct instead of
    /// identical (docs/72 section 2):
    ///
    /// * both basket sums iterate the basket **sorted**, and the sort is
    ///   ordinal -- Python's string order is by code point, and .NET's
    ///   default string comparison is culture-aware, which would reorder
    ///   the terms and change the last bit of the sum;
    /// * both sums are <see cref="CompensatedSum"/>, because the laboratory
    ///   writes them as <c>sum()</c>;
    /// * the multiplies in <see cref="WageRate"/> and
    ///   <see cref="ValueOfLaborPower"/> are **skipped**, not done by one.
    ///   The laboratory branches around them so that a model without the
    ///   rule reads the bits it always did; folding the branch away is the
    ///   kind of simplification that is right until someone changes the
    ///   neutral value.
    /// </summary>
    public static class WageSolver
    {
        /// <summary>
        /// The basket's names in the order both sums walk them: Python's
        /// <c>sorted()</c> over the dictionary's keys, which is ordinal.
        /// </summary>
        private static List<string> SortedBasketNames(RegionState region)
        {
            List<string> names = new List<string>();
            for (int i = 0; i < region.SubsistenceBasket.Count; i++)
            {
                names.Add(region.SubsistenceBasket[i].Name);
            }
            names.Sort(StringComparer.Ordinal);
            return names;
        }

        private static double BasketQuantity(RegionState region, string name)
        {
            for (int i = 0; i < region.SubsistenceBasket.Count; i++)
            {
                if (region.SubsistenceBasket[i].Name == name)
                {
                    return region.SubsistenceBasket[i].Amount;
                }
            }
            return 0.0;
        }

        /// <summary>
        /// Silver per worker-day: the basket at current prices.  The money
        /// form of the value of labor-power, with no premium on it.
        /// </summary>
        public static double BasketCost(RegionState region)
        {
            List<double> terms = new List<double>();
            foreach (string name in SortedBasketNames(region))
            {
                terms.Add(BasketQuantity(region, name) * region.PriceOf(name));
            }
            return CompensatedSum.Of(terms);
        }

        /// <summary>
        /// Silver per worker-day actually paid: the basket times one plus
        /// the premium (docs/46), and the basket itself when there is none.
        /// </summary>
        public static double WageRate(RegionState region)
        {
            double basket = BasketCost(region);
            if (region.WagePremium != 0.0)
            {
                return basket * (1.0 + region.WagePremium);
            }
            return basket;
        }

        /// <summary>
        /// Work-ticks to reproduce one worker-day: the basket at *social*
        /// labor values, because the value of labor-power is a social
        /// magnitude and not a regional one.  Names the region's basket
        /// carries that are not commodities are skipped, as in the
        /// laboratory's comprehension.
        /// </summary>
        public static double BasketLaborValue(WageProblem problem, RegionState region)
        {
            List<double> terms = new List<double>();
            foreach (string name in SortedBasketNames(region))
            {
                if (!problem.IsCommodity(name))
                {
                    continue;
                }
                terms.Add(BasketQuantity(region, name) * problem.LaborValueOf(name));
            }
            return CompensatedSum.Of(terms);
        }

        /// <summary>That, times the habitual standard where one has formed (docs/51).</summary>
        public static double ValueOfLaborPower(WageProblem problem, RegionState region)
        {
            double basket = BasketLaborValue(problem, region);
            if (region.HabitualScale == 1.0)
            {
                return basket;
            }
            return basket * region.HabitualScale;
        }

        /// <summary>
        /// Yesterday's employment as a fraction of the pool, and zero when
        /// the pool is unbounded: an unbounded reserve army is the limiting
        /// case in which the wage stays pinned to value (docs/46 section 2).
        /// </summary>
        public static double EmploymentRate(RegionState region)
        {
            if (!region.LaborPool.HasValue)
            {
                return 0.0;
            }
            return region.WorkerDaysEarned / region.LaborPool.Value;
        }

        /// <summary>
        /// What the paid wage carries above the *habitual* standard
        /// (docs/51): the whole premium while the standard is where it was
        /// seeded, and what habituation has not yet absorbed once it has
        /// moved.
        /// </summary>
        public static double PremiumOverValue(RegionState region)
        {
            if (region.HabitualScale == 1.0)
            {
                return region.WagePremium;
            }
            return (1.0 + region.WagePremium) / region.HabitualScale - 1.0;
        }

        /// <summary>
        /// The wage relation for one day (docs/17), given the labor that was
        /// performed.
        ///
        /// Employment is quantized to an exact binary grid so the daily
        /// basket flow adds to and subtracts from inventory without
        /// rounding -- the equilibrium must stay exact to the bit.  The
        /// division, the floor and the multiply are done in that order and
        /// not folded.
        ///
        /// This is the path *without* producer-level cash (docs/55), which
        /// is a later slice: the region pays the bill out of its own purse,
        /// and a region that cannot cover it is an error rather than a
        /// silent stop, because credit and bankruptcy are deliberately
        /// absent.  The four postings are returned as differences.
        /// </summary>
        public static Settlement Settle(
            WageProblem problem,
            RegionState region,
            LedgerTotals before,
            IEnumerable<LaborEntry> laborByProducer,
            double laborPerformed)
        {
            // `laborByProducer` is unread on this path and is here because
            // the producer-cash path (docs/55) divides the bill by it, and
            // that is the next slice rather than a different signature.
            Settlement settled = new Settlement();
            settled.After = before.Copy();
            double workerDays;
            if (problem.EmploymentQuantum > 0.0)
            {
                workerDays =
                    Math.Floor(
                        (laborPerformed / region.TicksPerWorkerDay)
                        / problem.EmploymentQuantum)
                    * problem.EmploymentQuantum;
            }
            else
            {
                workerDays = laborPerformed / region.TicksPerWorkerDay;
            }
            settled.WorkerDaysEarned = workerDays;
            if (region.SubsistenceBasket.Count == 0)
            {
                return settled;
            }

            double wageBill = workerDays * WageRate(region);
            if (wageBill > before.Cash)
            {
                throw new InvalidOperationException(
                    "region '" + region.Name + "' cannot cover its wage bill ("
                    + wageBill.ToString("F3", System.Globalization.CultureInfo.InvariantCulture)
                    + " silver against "
                    + before.Cash.ToString("F3", System.Globalization.CultureInfo.InvariantCulture)
                    + ")");
            }
            settled.After.Cash = before.Cash - wageBill;
            settled.After.WorkerCash = before.WorkerCash + wageBill;
            settled.After.WagesPaid = before.WagesPaid + wageBill;
            settled.After.LivingLabor = before.LivingLabor + laborPerformed;

            // The value of labor-power: the basket at endogenous social
            // labor values, so it moves when the conditions of producing
            // wage goods move.  This is what makes s/v an outcome rather
            // than a coefficient (docs/19 section 6).
            double necessaryPerDay = BasketLaborValue(problem, region);
            settled.After.NecessaryLabor =
                before.NecessaryLabor + workerDays * ValueOfLaborPower(problem, region);

            // The deviation of the wage from that value (docs/46), booked
            // apart from the necessary labor so the value of labor-power
            // never absorbs a bargained premium -- except through
            // habituation, which moves the line deliberately and leaves the
            // two summing to the wage as paid.
            if (region.WagePremium != 0.0 || region.HabitualScale != 1.0)
            {
                settled.After.WagePremiumPaid = before.WagePremiumPaid
                    + workerDays * BasketCost(region) * region.WagePremium;
                double deviation;
                if (region.HabitualScale == 1.0)
                {
                    deviation = necessaryPerDay * region.WagePremium;
                }
                else
                {
                    deviation = necessaryPerDay
                        * (1.0 + region.WagePremium - region.HabitualScale);
                }
                settled.After.WageDeviationLabor =
                    before.WageDeviationLabor + workerDays * deviation;
            }
            return settled;
        }
    }
}
