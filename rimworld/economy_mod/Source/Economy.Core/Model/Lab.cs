using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// The methods of the laboratory's <c>Process</c>, <c>Producer</c> and
    /// <c>Region</c> that the docked day calls, transliterated. They live
    /// here rather than on the generated classes so that regenerating the
    /// state never touches ported code.
    /// </summary>
    public static class Lab
    {
        public const double Epsilon = 1e-9;

        /// <summary>Python's two-argument <c>max</c>: the first unless the second is greater.</summary>
        public static double Max(double a, double b) { return b > a ? b : a; }

        /// <summary>Python's two-argument <c>min</c>: the first unless the second is less.</summary>
        public static double Min(double a, double b) { return b < a ? b : a; }

        /// <summary>CPython's <c>sum()</c>.</summary>
        public static double Sum(List<double> terms) { return CompensatedSum.Of(terms); }

        // ---- Process ---------------------------------------------------

        public static double RunsFor(Process p, double capacityPerDay)
        {
            return capacityPerDay / Max(p.CapacityPerRun, Epsilon);
        }

        /// <summary><c>capital_bill_per_capacity</c>: sorted by name.</summary>
        public static OrderedMap<double> CapitalBillPerCapacity(Process p)
        {
            OrderedMap<double> bill = new OrderedMap<double>();
            foreach (string name in p.CapitalBill.SortedKeys())
            {
                bill[name] = p.CapitalBill[name] * p.MachinesPerCapacity;
            }
            return bill;
        }

        /// <summary><c>input_cost_per_run</c>: insertion order, CPython's sum.</summary>
        public static double InputCostPerRun(Process p, OrderedMap<double> prices)
        {
            List<double> terms = new List<double>(p.Inputs.Count);
            for (int i = 0; i < p.Inputs.Count; i++)
            {
                terms.Add(p.Inputs.ValueAt(i) * prices.Get(p.Inputs.KeyAt(i), 0.0));
            }
            return Sum(terms);
        }

        /// <summary><c>share_of_cost</c>: mass apportionment (docs/08).</summary>
        public static double ShareOfCost(Process p, string commodity, OrderedMap<Commodity> commodities)
        {
            if (!p.Outputs.ContainsKey(commodity))
            {
                return 0.0;
            }
            if (p.Outputs.Count == 1)
            {
                return 1.0;
            }
            if (p.Apportionment != "mass")
            {
                throw new System.ArgumentException("unknown apportionment rule '" + p.Apportionment + "'");
            }
            List<double> weights = new List<double>(p.Outputs.Count);
            for (int i = 0; i < p.Outputs.Count; i++)
            {
                weights.Add(MassWeight(p, p.Outputs.KeyAt(i), commodities));
            }
            double total = Sum(weights);
            if (total <= Epsilon)
            {
                return 1.0 / p.Outputs.Count;
            }
            return MassWeight(p, commodity, commodities) / total;
        }

        private static double MassWeight(Process p, string name, OrderedMap<Commodity> commodities)
        {
            Commodity good;
            double mass = commodities.TryGetValue(name, out good) ? good.MassPerUnit : 1.0;
            return mass * p.Outputs[name];
        }

        /// <summary><c>labor_per_unit</c>.</summary>
        public static double LaborPerUnit(Process p, string commodity, OrderedMap<Commodity> commodities)
        {
            double units = p.Outputs.Get(commodity, 0.0);
            if (units <= Epsilon)
            {
                return 0.0;
            }
            return p.DirectLabor * ShareOfCost(p, commodity, commodities) / units;
        }

        /// <summary><c>capital_consumed_per_unit</c> with both overrides passed.</summary>
        public static void CapitalConsumedPerUnit(Process p, string commodity, double serviceLifeDays,
            OrderedMap<Commodity> commodities, double moneyPerCapacity, double laborPerCapacity,
            out double money, out double labor)
        {
            money = 0.0;
            labor = 0.0;
            if (serviceLifeDays <= Epsilon)
            {
                return;
            }
            double share = ShareOfCost(p, commodity, commodities);
            double units = p.Outputs.Get(commodity, 0.0);
            if (units <= Epsilon)
            {
                return;
            }
            money = moneyPerCapacity * share / serviceLifeDays;
            labor = laborPerCapacity * share / serviceLifeDays;
        }

        // ---- Producer --------------------------------------------------

        /// <summary><c>effective_unit_cost</c>.</summary>
        public static double EffectiveUnitCost(Producer p, OrderedMap<double> prices)
        {
            double inputCost = InputCostPerRun(p.Process, prices);
            double outputPerRun = p.Process.Outputs.Get(p.Commodity, 0.0);
            if (outputPerRun <= Epsilon)
            {
                return p.UnitCost + p.WageCostPerUnit;
            }
            return p.UnitCost + inputCost / outputPerRun + p.WageCostPerUnit;
        }

        /// <summary><c>utilization</c>, with today's prices passed.</summary>
        public static double Utilization(Producer p, double price, OrderedMap<double> prices)
        {
            if (!p.Active || p.CapacityPerDay <= 0)
            {
                return 0.0;
            }
            double cost = EffectiveUnitCost(p, prices);
            double ratio = price / Max(cost, Epsilon);
            if (ratio <= p.ZeroUtilizationPriceRatio)
            {
                return 0.0;
            }
            if (ratio >= p.FullUtilizationPriceRatio)
            {
                return 1.0;
            }
            double span = p.FullUtilizationPriceRatio - p.ZeroUtilizationPriceRatio;
            return (ratio - p.ZeroUtilizationPriceRatio) / Max(span, Epsilon);
        }

        /// <summary><c>desired_runs</c>.</summary>
        public static double DesiredRuns(Producer p, double price, OrderedMap<double> prices)
        {
            return RunsFor(p.Process, p.CapacityPerDay) * Utilization(p, price, prices);
        }

        /// <summary>A copy of a map, as <c>dict(m)</c>.</summary>
        public static OrderedMap<double> Copy(OrderedMap<double> map)
        {
            OrderedMap<double> copy = new OrderedMap<double>();
            for (int i = 0; i < map.Count; i++)
            {
                copy[map.KeyAt(i)] = map.ValueAt(i);
            }
            return copy;
        }

        // ---- Region ----------------------------------------------------

        /// <summary><c>full_capacity_labor_ticks</c>.</summary>
        public static double FullCapacityLaborTicks(Region region)
        {
            List<double> terms = new List<double>();
            foreach (Producer p in region.Producers)
            {
                if (p.Active)
                {
                    terms.Add(RunsFor(p.Process, p.CapacityPerDay) * p.Process.DirectLabor);
                }
            }
            return Sum(terms);
        }

        /// <summary><c>throughput_demands</c>.</summary>
        public static OrderedMap<double> ThroughputDemands(Region region)
        {
            OrderedMap<List<double>> terms = new OrderedMap<List<double>>();
            foreach (Producer producer in region.Producers)
            {
                if (!producer.Active)
                {
                    continue;
                }
                double runs = RunsFor(producer.Process, producer.CapacityPerDay);
                OrderedMap<double> inputs = producer.Process.Inputs;
                for (int i = 0; i < inputs.Count; i++)
                {
                    double perRun = inputs.ValueAt(i);
                    if (perRun > 0)
                    {
                        terms.SetDefault(inputs.KeyAt(i), new List<double>()).Add(runs * perRun);
                    }
                }
                OrderedMap<double> bill = CapitalBillPerCapacity(producer.Process);
                for (int i = 0; i < bill.Count; i++)
                {
                    double quantity = bill.ValueAt(i);
                    if (quantity > 0)
                    {
                        terms.SetDefault(bill.KeyAt(i), new List<double>()).Add(
                            producer.CapacityPerDay * quantity / Max(region.CapitalServiceLifeDays, Epsilon));
                    }
                }
            }
            double workers = FullCapacityLaborTicks(region) / Max(region.TicksPerWorkerDay, Epsilon);
            OrderedMap<double> totals = new OrderedMap<double>();
            for (int i = 0; i < region.Prices.Count; i++)
            {
                string name = region.Prices.KeyAt(i);
                double basis = region.BaseDailyDemand.Get(name, 0.0);
                if (region.MoneyDemand.Count > 0 && basis > 0.0)
                {
                    basis = region.MoneyDemand.Get(name, 0.0);
                }
                List<double> mine;
                double total = basis + (terms.TryGetValue(name, out mine) ? Sum(mine) : 0.0);
                double quantity = region.SubsistenceBasket.Get(name, 0.0);
                if (quantity > 0.0)
                {
                    if (region.HabitualScale != 1.0)
                    {
                        quantity = quantity * region.HabitualScale;
                    }
                    total += quantity * workers;
                }
                totals[name] = total;
            }
            return totals;
        }

        /// <summary><c>basket_cost</c>: the basket at current prices, sorted by name.</summary>
        public static double BasketCost(Region region)
        {
            List<double> terms = new List<double>();
            foreach (string name in region.SubsistenceBasket.SortedKeys())
            {
                terms.Add(region.SubsistenceBasket[name] * region.Prices.Get(name, 0.0));
            }
            return Sum(terms);
        }

        /// <summary><c>wage_rate</c>.</summary>
        public static double WageRate(Region region)
        {
            double basket = BasketCost(region);
            if (region.WagePremium != 0.0)
            {
                return basket * (1.0 + region.WagePremium);
            }
            return basket;
        }

        /// <summary><c>daily_demand</c>, the money-demand branch only: the
        /// docked fund always sets it (docs/132 s2), and the other branch
        /// raises to a power, which the port avoids until it must.</summary>
        public static double DailyDemand(Region region, Commodity commodity)
        {
            double basis = region.BaseDailyDemand.Get(commodity.Name, 0.0);
            if (basis <= 0)
            {
                return 0.0;
            }
            if (region.MoneyDemand.Count > 0)
            {
                return region.MoneyDemand.Get(commodity.Name, 0.0);
            }
            throw new NotSupportedException("daily_demand without money demand is not carried (docs/141 s2)");
        }
    }
}
