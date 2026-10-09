using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary>One seller's share of a commodity's sales.</summary>
        internal struct Share
        {
            public readonly Producer Producer;
            public readonly double Fraction;

            public Share(Producer producer, double fraction)
            {
                Producer = producer;
                Fraction = fraction;
            }
        }

        /// <summary><c>_consume</c>: final demand, paid for by the fund (docs/55).</summary>
        public static void Consume(EconomyState e)
        {
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                Dictionary<string, List<Share>> shares = SupplyShares(e, region);
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    Commodity commodity = e.Commodities.ValueAt(c);
                    string name = commodity.Name;
                    double desired = Lab.DailyDemand(region, commodity);
                    double available = region.Inventory[name];
                    double consumed = Lab.Min(desired, available);
                    double price = region.Prices[name];
                    double affordable = region.Cash / Lab.Max(price, Epsilon);
                    if (consumed > affordable)
                    {
                        consumed = Lab.Max(0.0, affordable);
                    }
                    double credited = PaySellers(e, region, name, consumed * price, shares, true, consumed);
                    region.Cash -= credited;
                    double unmet = desired - consumed;
                    region.Inventory[name] = region.Inventory[name] - consumed;
                    region.UnmetDemand[name] = region.UnmetDemand[name] + unmet;
                    region.ConsumedTotal[name] = region.ConsumedTotal[name] + consumed;
                    Add(e.Ledger.Consumption, name, consumed);
                }
            }
        }

        /// <summary><c>_supply_shares</c>: by realized output, or by capacity
        /// where nobody ran (docs/55). Looked up by commodity only, so a
        /// plain dictionary carries it.</summary>
        internal static Dictionary<string, List<Share>> SupplyShares(EconomyState e, Region region)
        {
            Dictionary<string, List<Share>> shares = new Dictionary<string, List<Share>>(System.StringComparer.Ordinal);
            // One pass groups the active producers by commodity, each group
            // in region order: the lists the laboratory's per-commodity
            // scan builds, without scanning every producer per commodity.
            Dictionary<string, List<Producer>> byCommodity = new Dictionary<string, List<Producer>>(System.StringComparer.Ordinal);
            foreach (Producer p in region.Producers)
            {
                if (!p.Active)
                {
                    continue;
                }
                List<Producer> group;
                if (!byCommodity.TryGetValue(p.Commodity, out group))
                {
                    group = new List<Producer>();
                    byCommodity[p.Commodity] = group;
                }
                group.Add(p);
            }
            for (int c = 0; c < e.Commodities.Count; c++)
            {
                string name = e.Commodities.KeyAt(c);
                List<Producer> producers;
                if (!byCommodity.TryGetValue(name, out producers))
                {
                    continue;
                }
                List<double> weights = new List<double>(producers.Count);
                foreach (Producer p in producers)
                {
                    weights.Add(p.LastRuns * p.Process.Outputs.Get(name, 0.0));
                }
                double total = Lab.Sum(weights);
                if (total <= Epsilon && !e.SalesFollowProduction)
                {
                    weights.Clear();
                    foreach (Producer p in producers)
                    {
                        weights.Add(p.CapacityPerDay);
                    }
                    total = Lab.Sum(weights);
                }
                if (total <= Epsilon)
                {
                    continue;
                }
                List<Share> list = new List<Share>();
                for (int i = 0; i < producers.Count; i++)
                {
                    if (weights[i] > 0.0)
                    {
                        list.Add(new Share(producers[i], weights[i] / total));
                    }
                }
                shares[name] = list;
            }
            return shares;
        }

        /// <summary><c>_pay_sellers</c>, the posted-price branch: each seller
        /// is paid what it posted on its share of the units (docs/57).</summary>
        internal static double PaySellers(EconomyState e, Region region, string commodity, double amount,
            Dictionary<string, List<Share>> shares, bool buyerIsFund, double units)
        {
            if (amount <= 0.0)
            {
                return 0.0;
            }
            List<Share> sellers;
            if (!shares.TryGetValue(commodity, out sellers) || sellers.Count == 0)
            {
                if (buyerIsFund)
                {
                    return 0.0;
                }
                region.Cash += amount;
                return amount;
            }
            double credited = 0.0;
            foreach (Share seller in sellers)
            {
                double paid = units * seller.Fraction * seller.Producer.PostedPrice;
                seller.Producer.Cash += paid;
                credited += paid;
            }
            Add(e.Ledger.SalesReceipts, region.Name, credited);
            return credited;
        }

        /// <summary><c>_workers_consume</c>: yesterday's wages on the basket.</summary>
        public static void WorkersConsume(EconomyState e)
        {
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                if (region.SubsistenceBasket.Count > 0)
                {
                    double workerDays = region.WorkerDaysDue;
                    Dictionary<string, List<Share>> basketShares = SupplyShares(e, region);
                    List<string> names = new List<string>();
                    List<double> boughts = new List<double>();
                    List<double> prices = new List<double>();
                    double totalCost = 0.0;
                    foreach (string name in region.SubsistenceBasket.SortedKeys())
                    {
                        if (!e.Commodities.ContainsKey(name))
                        {
                            continue;
                        }
                        double desired = region.SubsistenceBasket[name] * workerDays;
                        if (region.WagePremiumDue != 0.0)
                        {
                            desired *= 1.0 + region.WagePremiumDue;
                        }
                        if (desired <= 0.0)
                        {
                            continue;
                        }
                        double bought = Lab.Min(desired, region.Inventory.Get(name, 0.0));
                        double inventoryShortfall = desired - bought;
                        if (inventoryShortfall > Epsilon)
                        {
                            region.UnmetDemand[name] = region.UnmetDemand[name] + inventoryShortfall;
                            Add(e.Ledger.BasketShortfall, region.Name, inventoryShortfall);
                        }
                        if (bought <= 0.0)
                        {
                            continue;
                        }
                        names.Add(name);
                        boughts.Add(bought);
                        prices.Add(region.Prices[name]);
                        totalCost += bought * region.Prices[name];
                    }
                    double cashFactor = 1.0;
                    if (totalCost > region.WorkerCash)
                    {
                        cashFactor = region.WorkerCash / totalCost;
                    }
                    for (int i = 0; i < names.Count; i++)
                    {
                        string name = names[i];
                        double bought = boughts[i];
                        double price = prices[i];
                        if (cashFactor < 1.0)
                        {
                            double affordable = bought * cashFactor;
                            double denied = bought - affordable;
                            region.UnmetDemand[name] = region.UnmetDemand[name] + denied;
                            Add(e.Ledger.BasketShortfall, region.Name, denied);
                            bought = affordable;
                        }
                        if (bought <= 0.0)
                        {
                            continue;
                        }
                        double spend = bought * price;
                        region.Inventory[name] = region.Inventory[name] - bought;
                        region.ConsumedTotal[name] = region.ConsumedTotal[name] + bought;
                        Add(e.Ledger.Consumption, name, bought);
                        spend = PaySellers(e, region, name, spend, basketShares, false, bought);
                        region.WorkerCash -= spend;
                        Add(e.Ledger.WorkerSpending, region.Name, spend);
                    }
                }
                region.WorkerDaysDue = region.WorkerDaysEarned;
                region.WagePremiumDue = region.WagePremium;
            }
        }
    }
}
