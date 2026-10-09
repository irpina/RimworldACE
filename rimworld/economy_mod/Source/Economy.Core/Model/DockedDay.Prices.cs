using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary><c>_update_prices</c>, which docked is always the posted
        /// branch: <c>_update_posted_prices</c> without procurement (docs/57,
        /// docs/58).</summary>
        public static void UpdatePrices(EconomyState e)
        {
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                OrderedMap<double> opening = Lab.Copy(region.Prices);
                Dictionary<Producer, double> costs = new Dictionary<Producer, double>();
                foreach (Producer p in region.Producers)
                {
                    if (p.Active)
                    {
                        costs[p] = Lab.EffectiveUnitCost(p, opening);
                    }
                }
                OrderedMap<double> throughput = e.Throughput[region.Name];
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    Commodity commodity = e.Commodities.ValueAt(c);
                    string name = commodity.Name;
                    double pressure;
                    if (!PoolPressure(e, region, commodity, out pressure))
                    {
                        continue;
                    }
                    List<Producer> producers = new List<Producer>();
                    foreach (Producer p in region.Producers)
                    {
                        if (p.Active && p.Commodity == name)
                        {
                            producers.Add(p);
                        }
                    }
                    if (producers.Count == 0)
                    {
                        continue;
                    }
                    List<double> fills = new List<double>(producers.Count);
                    foreach (Producer p in producers)
                    {
                        fills.Add(p.OrderFill);
                    }
                    double meanFill = Lab.Sum(fills) / producers.Count;
                    // Computed and unused when docked, as in the laboratory;
                    // kept so that a missing key fails here as it does there.
                    double unmetTerm = e.UnmetDemandPricePressure * region.UnmetDemand[name]
                        / Lab.Max(throughput[name], Epsilon);
                    foreach (Producer producer in producers)
                    {
                        double cost = costs[producer];
                        double posted = producer.PostedPrice;
                        if (producer.LastCost > Epsilon && cost != producer.LastCost)
                        {
                            posted *= cost / producer.LastCost;
                        }
                        double own = pressure + e.PostedShareGain * (producer.OrderFill - meanFill);
                        if (own != 0.0)
                        {
                            posted *= Math.Exp(e.PostedPriceSpeed * own);
                        }
                        double low = cost * Lab.Max(commodity.MinimumPriceFactor, 0.0);
                        double high = cost * commodity.MaximumPriceFactor;
                        if (cost > Epsilon)
                        {
                            posted = Lab.Min(high, Lab.Max(low, posted));
                        }
                        producer.PostedPrice = posted;
                        producer.LastCost = cost;
                    }
                    List<double> weights = new List<double>(producers.Count);
                    List<double> asked = new List<double>(producers.Count);
                    foreach (Producer p in producers)
                    {
                        weights.Add(p.LastRuns * p.Process.Outputs.Get(name, 0.0));
                        asked.Add(p.PostedPrice);
                    }
                    double total = Lab.Sum(weights);
                    if (total <= Epsilon)
                    {
                        weights.Clear();
                        asked.Clear();
                        foreach (Producer p in producers)
                        {
                            weights.Add(p.CapacityPerDay);
                            asked.Add(p.PostedPrice);
                        }
                        total = Lab.Sum(weights);
                    }
                    if (total <= Epsilon)
                    {
                        continue;
                    }
                    if (weights.Count == 1)
                    {
                        region.Prices[name] = asked[0];
                    }
                    else
                    {
                        List<double> products = new List<double>(weights.Count);
                        for (int i = 0; i < weights.Count; i++)
                        {
                            products.Add(weights[i] * asked[i]);
                        }
                        region.Prices[name] = Lab.Sum(products) / total;
                    }
                }
            }
        }

        /// <summary><c>_pool_pressure</c>: false where the commodity is not
        /// traded here, the laboratory's <c>None</c>.</summary>
        private static bool PoolPressure(EconomyState e, Region region, Commodity commodity, out double pressure)
        {
            string name = commodity.Name;
            double throughput = e.Throughput[region.Name][name];
            pressure = 0.0;
            if (throughput <= Epsilon)
            {
                return false;
            }
            double target = throughput * commodity.TargetInventoryDays;
            double coverageGap = (target - region.Inventory[name]) / Lab.Max(target, Epsilon);
            double unmetRatio = region.UnmetDemand[name] / throughput;
            pressure = commodity.InventoryPriceSensitivity * coverageGap
                + e.UnmetDemandPricePressure * unmetRatio;
            return true;
        }
    }
}
