using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary><c>_refresh_throughput</c>: the fund decides today's
        /// final demand, then every region's throughput is rebuilt.</summary>
        public static void RefreshThroughput(EconomyState e)
        {
            if (e.FundSpendingRate > 0.0)
            {
                for (int r = 0; r < e.Regions.Count; r++)
                {
                    SpendTheFund(e, e.Regions.ValueAt(r));
                }
            }
            OrderedMap<OrderedMap<double>> throughput = new OrderedMap<OrderedMap<double>>();
            for (int r = 0; r < e.Regions.Count; r++)
            {
                throughput[e.Regions.KeyAt(r)] = Lab.ThroughputDemands(e.Regions.ValueAt(r));
            }
            e.Throughput = throughput;
        }

        /// <summary><c>_spend_the_fund</c> (docs/132 s2): a share of the
        /// fund's silver, split by value shares fixed on the first call.</summary>
        private static void SpendTheFund(EconomyState e, Region region)
        {
            if (region.SpendingShares.Count == 0)
            {
                OrderedMap<double> values = new OrderedMap<double>();
                foreach (string name in region.BaseDailyDemand.SortedKeys())
                {
                    double basis = region.BaseDailyDemand[name];
                    if (basis > 0.0)
                    {
                        values[name] = basis * region.Prices.Get(name, 0.0);
                    }
                }
                List<double> terms = new List<double>();
                for (int i = 0; i < values.Count; i++)
                {
                    terms.Add(values.ValueAt(i));
                }
                double total = Lab.Sum(terms);
                if (total <= Epsilon)
                {
                    return;
                }
                OrderedMap<double> shares = new OrderedMap<double>();
                for (int i = 0; i < values.Count; i++)
                {
                    shares[values.KeyAt(i)] = values.ValueAt(i) / total;
                }
                region.SpendingShares = shares;
                region.AuthoredValue = total;
            }
            double money = e.FundSpendingRate * Lab.Max(region.Cash, 0.0);
            region.DemandScale = money / Lab.Max(region.AuthoredValue, Epsilon);
            OrderedMap<double> demand = new OrderedMap<double>();
            for (int i = 0; i < region.SpendingShares.Count; i++)
            {
                string name = region.SpendingShares.KeyAt(i);
                demand[name] = money * region.SpendingShares.ValueAt(i) / Lab.Max(region.Prices.Get(name, 0.0), Epsilon);
            }
            region.MoneyDemand = demand;
        }
    }
}
