namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary><c>_update_cost_ratios</c> as the step calls it: from the
        /// day's realized runs, against each sector's seeded cost (docs/21).</summary>
        public static void UpdateCostRatios(EconomyState e)
        {
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    string name = e.Commodities.KeyAt(c);
                    double cost;
                    bool produced = SectorUnitCost(region, name, out cost);
                    double seed;
                    bool seeded = region.SeedUnitCost.TryGetValue(name, out seed);
                    if (!produced || !seeded || seed <= Epsilon)
                    {
                        region.CostRatio.SetDefault(name, 1.0);
                        continue;
                    }
                    region.CostRatio[name] = cost / seed;
                }
            }
        }

        /// <summary><c>_sector_unit_cost</c> from realized runs; false is the
        /// laboratory's <c>None</c>, nobody produced.</summary>
        private static bool SectorUnitCost(Region region, string commodity, out double cost)
        {
            double totalCost = 0.0;
            double totalOutput = 0.0;
            foreach (Producer producer in region.Producers)
            {
                if (!producer.Active || producer.Commodity != commodity)
                {
                    continue;
                }
                double runs = producer.LastRuns;
                if (runs <= Epsilon)
                {
                    continue;
                }
                double output = runs * producer.Process.Outputs.Get(commodity, 0.0);
                if (output <= Epsilon)
                {
                    continue;
                }
                totalCost += output * Lab.EffectiveUnitCost(producer, region.Prices);
                totalOutput += output;
            }
            cost = 0.0;
            if (totalOutput <= Epsilon)
            {
                return false;
            }
            cost = totalCost / totalOutput;
            return true;
        }
    }
}
