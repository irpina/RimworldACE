using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>A commodity as the price rule reads it.</summary>
    public sealed class CommoditySpec
    {
        public string Name;
        public double ReferencePrice;
        public double TargetInventoryDays;
        public double InventoryPriceSensitivity;
        public double MinimumPriceFactor;
        public double MaximumPriceFactor;
        public double PriceAdjustmentSpeed;
    }

    /// <summary>One region's books as the price rule reads them.</summary>
    public sealed class PriceRegion
    {
        public string Name;
        public Dictionary<string, double> Throughput = new Dictionary<string, double>();
        public Dictionary<string, double> Inventory = new Dictionary<string, double>();
        public Dictionary<string, double> UnmetDemand = new Dictionary<string, double>();
        /// <summary>
        /// The sector's cost against its seeded cost.  A **missing** entry
        /// is exactly 1.0, which makes the anchor exactly the reference
        /// price; defaulting to zero instead would move the anchor to
        /// <c>reference * (1 - kappa)</c> and the equilibrium would drift
        /// on the first day (docs/77 section 3).
        /// </summary>
        public Dictionary<string, double> CostRatio = new Dictionary<string, double>();
        public Dictionary<string, double> Prices = new Dictionary<string, double>();
    }

    /// <summary>What the price rule reads that is not regional.</summary>
    public sealed class PriceProblem
    {
        public double CompetitivePriceIntensity;
        public double UnmetDemandPricePressure;
        /// <summary>In the model's order, which is the order the rule walks.</summary>
        public List<CommoditySpec> Commodities = new List<CommoditySpec>();
        public List<PriceRegion> Regions = new List<PriceRegion>();
    }

    /// <summary>
    /// The planned model's regional price rule (docs/21), ported from
    /// <c>Economy._update_prices</c>'s non-posted branch (docs/77).
    ///
    /// **This slice contains the port's first transcendental.** IEEE 754
    /// specifies every other operation here to the bit; it does not
    /// specify <c>exp</c>, and no common libm promises correct rounding
    /// for it. Where every earlier slice could claim bit-exactness as a
    /// property of the arithmetic, this one can only measure it against
    /// whatever <c>exp</c> the runtime carries. docs/78 reports what was
    /// measured.
    ///
    /// The one safe case is worth knowing: at the seed the pressure is
    /// exactly zero and every libm returns exactly 1.0 for
    /// <c>exp(0.0)</c>, so a stationary circuit stays stationary whatever
    /// else disagrees.
    /// </summary>
    public static class PriceSolver
    {
        private const double Epsilon = 1e-9;

        public static void UpdatePrices(PriceProblem problem)
        {
            foreach (PriceRegion region in problem.Regions)
            {
                foreach (CommoditySpec commodity in problem.Commodities)
                {
                    string name = commodity.Name;
                    double throughput = Get(region.Throughput, name, 0.0);
                    if (throughput <= Epsilon)
                    {
                        // Neither consumed nor used as an input here. That
                        // is "not traded in this region", not "infinitely
                        // oversupplied", so leave the price alone instead
                        // of driving it to the floor on a division by
                        // nothing.
                        continue;
                    }
                    double baseDemand = throughput;
                    double target = baseDemand * commodity.TargetInventoryDays;
                    double coverageGap =
                        (target - Get(region.Inventory, name, 0.0))
                        / Math.Max(target, Epsilon);
                    double unmetRatio = Get(region.UnmetDemand, name, 0.0) / baseDemand;
                    double pressure =
                        commodity.InventoryPriceSensitivity * coverageGap
                        + problem.UnmetDemandPricePressure * unmetRatio;
                    double old = Get(region.Prices, name, 0.0);
                    double low = commodity.ReferencePrice * commodity.MinimumPriceFactor;
                    double high = commodity.ReferencePrice * commodity.MaximumPriceFactor;
                    // The anchor moves with the sector's cost relative to
                    // its seeded cost (docs/21).  Written in this form
                    // because `1 + kappa * (ratio - 1)` is exactly 1.0 when
                    // the ratio is exactly 1.0, for any kappa, which is what
                    // keeps the four-year equilibrium price range at
                    // exactly zero.
                    double anchor = commodity.ReferencePrice
                        * (1.0
                           + problem.CompetitivePriceIntensity
                             * (Get(region.CostRatio, name, 1.0) - 1.0));
                    anchor = Math.Max(anchor, low);
                    double desired = anchor * Math.Exp(pressure);
                    desired = Math.Min(high, Math.Max(low, desired));
                    region.Prices[name] =
                        old + commodity.PriceAdjustmentSpeed * (desired - old);
                }
            }
        }

        private static double Get(
            Dictionary<string, double> mapping, string key, double fallback)
        {
            double value;
            return mapping.TryGetValue(key, out value) ? value : fallback;
        }
    }
}
