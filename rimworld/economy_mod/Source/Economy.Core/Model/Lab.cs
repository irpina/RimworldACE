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
