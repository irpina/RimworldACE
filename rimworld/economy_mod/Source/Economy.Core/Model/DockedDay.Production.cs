using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary>
        /// <c>_produce</c> without procurement, reserves or bills of
        /// materials: plan against the opening stock, ration by matter,
        /// labor and purse, produce simultaneously, pay for the draws, wear
        /// the plant (rule two), and settle the day's labor.
        /// </summary>
        public static void Produce(EconomyState e)
        {
            e.HasDailyExtraction = true;
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                List<Producer> active = OpenRegionDay(e, region);
                OrderedMap<double> opening = Lab.Copy(region.Inventory);
                Dictionary<Producer, double> desired = new Dictionary<Producer, double>();
                foreach (Producer p in active)
                {
                    desired[p] = Lab.DesiredRuns(p, region.Prices[p.Commodity], region.Prices);
                }
                Dictionary<Producer, double> planned = PlannedRuns(e, region, opening, active, desired);
                foreach (Producer p in active)
                {
                    double offered = desired[p];
                    p.OrderFill = offered > Epsilon ? planned[p] / offered : 1.0;
                }

                OrderedMap<double> required = new OrderedMap<double>();
                foreach (Producer producer in active)
                {
                    double runs = planned[producer];
                    OrderedMap<double> inputs = producer.Process.Inputs;
                    for (int i = 0; i < inputs.Count; i++)
                    {
                        string name = inputs.KeyAt(i);
                        required[name] = required.Get(name, 0.0) + runs * inputs.ValueAt(i);
                    }
                }
                foreach (Producer producer in active)
                {
                    double perCapacity = producer.CapacityPerDay / e.CapitalServiceLifeDays;
                    OrderedMap<double> bill = Lab.CapitalBillPerCapacity(producer.Process);
                    for (int i = 0; i < bill.Count; i++)
                    {
                        string name = bill.KeyAt(i);
                        required[name] = required.Get(name, 0.0) + perCapacity * bill.ValueAt(i);
                    }
                }
                OrderedMap<double> ration = new OrderedMap<double>();
                for (int i = 0; i < required.Count; i++)
                {
                    string name = required.KeyAt(i);
                    double need = required.ValueAt(i);
                    ration[name] = need <= Epsilon ? 1.0 : Lab.Min(1.0, opening.Get(name, 0.0) / need);
                }

                if (!double.IsPositiveInfinity(region.LaborPool))
                {
                    double availableTicks = region.LaborPool * region.TicksPerWorkerDay;
                    List<double> ticks = new List<double>(active.Count);
                    foreach (Producer p in active)
                    {
                        ticks.Add(planned[p] * p.Process.DirectLabor);
                    }
                    double plannedTicks = Lab.Sum(ticks);
                    if (plannedTicks > availableTicks)
                    {
                        double laborRation = availableTicks / plannedTicks;
                        foreach (Producer p in active)
                        {
                            planned[p] *= laborRation;
                        }
                    }
                }

                Dictionary<string, List<Share>> yesterday = SupplyShares(e, region);
                foreach (Producer p in active)
                {
                    double wanted = planned[p];
                    if (wanted <= Epsilon)
                    {
                        continue;
                    }
                    double perRun = OutlayPerRun(p, region);
                    double spendable = p.Cash - PlantMatterCost(e, p, region);
                    if (perRun <= Epsilon)
                    {
                        continue;
                    }
                    double affordable = Lab.Max(0.0, spendable) / perRun;
                    if (e.ProducerEmploymentQuantum > 0.0)
                    {
                        affordable = QuantizeEmployment(e, p, region, affordable);
                    }
                    if (affordable < wanted)
                    {
                        Add(e.Ledger.LiquidityCurtailment, p.Commodity, wanted - affordable);
                        planned[p] = affordable;
                    }
                    if (affordable <= Epsilon)
                    {
                        p.LiquidityIdleDays += 1;
                    }
                    else
                    {
                        p.LiquidityIdleDays = 0;
                    }
                }

                OrderedMap<double> drawn = new OrderedMap<double>();
                OrderedMap<double> produced = new OrderedMap<double>();
                Dictionary<Producer, double> laborByProducer = new Dictionary<Producer, double>();
                double laborPerformed = 0.0;
                foreach (Producer producer in region.Producers)
                {
                    producer.LastRuns = 0.0;
                }
                foreach (Producer producer in active)
                {
                    double runs = planned[producer];
                    if (runs <= Epsilon)
                    {
                        continue;
                    }
                    OrderedMap<double> inputs = producer.Process.Inputs;
                    double available = 1.0;
                    for (int i = 0; i < inputs.Count; i++)
                    {
                        double share = ration[inputs.KeyAt(i)];
                        available = i == 0 ? share : Lab.Min(available, share);
                    }
                    runs *= available;
                    if (runs <= Epsilon)
                    {
                        continue;
                    }
                    producer.LastRuns = runs;
                    laborPerformed += runs * producer.Process.DirectLabor;
                    laborByProducer[producer] = runs * producer.Process.DirectLabor;
                    double ownOutput = runs * producer.Process.Outputs.Get(producer.Commodity, 0.0);
                    if (ownOutput > Epsilon)
                    {
                        Add(e.Ledger.FixedCapitalConsumed, region.Name, ownOutput * producer.CapitalLaborPerUnit);
                        Add(e.Ledger.FixedCapitalMoney, region.Name, ownOutput * producer.CapitalCostPerUnit);
                        Add(e.Ledger.UnattributedMargin, region.Name, ownOutput * (producer.UnitCost - producer.CapitalCostPerUnit));
                    }
                    for (int i = 0; i < inputs.Count; i++)
                    {
                        string name = inputs.KeyAt(i);
                        drawn[name] = drawn.Get(name, 0.0) + runs * inputs.ValueAt(i);
                    }
                    OrderedMap<double> outputs = producer.Process.Outputs;
                    for (int i = 0; i < outputs.Count; i++)
                    {
                        string name = outputs.KeyAt(i);
                        if (!e.Commodities.ContainsKey(name))
                        {
                            continue;
                        }
                        produced[name] = produced.Get(name, 0.0) + runs * outputs.ValueAt(i);
                    }
                    producer.OutputTotal += runs * producer.Process.Outputs.Get(producer.Commodity, 0.0);
                }
                foreach (Producer producer in active)
                {
                    double construction = ReplacePlant(e, region, producer, ration, drawn);
                    laborPerformed += construction;
                    if (construction > 0.0)
                    {
                        double before;
                        laborByProducer.TryGetValue(producer, out before);
                        laborByProducer[producer] = before + construction;
                    }
                }
                PayForDraws(e, region, active, ration, yesterday);
                ShedCapacity(e, region, active);
                for (int i = 0; i < drawn.Count; i++)
                {
                    string name = drawn.KeyAt(i);
                    double amount = drawn.ValueAt(i);
                    region.Inventory[name] = region.Inventory[name] - amount;
                    Add(e.Ledger.IntermediateConsumption, name, amount);
                    Add(e.Ledger.CirculatingCapital, region.Name, amount * e.LaborValues.Get(name, 0.0));
                }
                for (int i = 0; i < produced.Count; i++)
                {
                    string name = produced.KeyAt(i);
                    double amount = produced.ValueAt(i);
                    region.Inventory[name] = region.Inventory[name] + amount;
                    Add(e.Ledger.Production, name, amount);
                    Add(e.Ledger.ValueProduced, region.Name, amount * e.LaborValues.Get(name, 0.0));
                }
                for (int i = 0; i < required.Count; i++)
                {
                    string name = required.KeyAt(i);
                    double shortfall = required.ValueAt(i) * (1.0 - ration[name]);
                    if (shortfall > Epsilon)
                    {
                        region.UnmetDemand[name] = region.UnmetDemand[name] + shortfall;
                    }
                }
                SettleLabor(e, region, active, laborByProducer, laborPerformed);
            }
        }

        /// <summary><c>_open_region_day</c>: the steps every day opens with,
        /// and the active producers sorted by name.</summary>
        private static List<Producer> OpenRegionDay(EconomyState e, Region region)
        {
            for (int c = 0; c < e.Commodities.Count; c++)
            {
                region.UnmetDemand[e.Commodities.KeyAt(c)] = 0.0;
            }
            foreach (Producer producer in region.Producers)
            {
                if (producer.Active)
                {
                    SetCapitalConsumption(e, producer, region);
                }
            }
            // _bargain and _habituate return at once: both strengths are
            // zero when docked, which Refuse has already checked.
            UpdateWageCosts(e, region);
            foreach (Producer producer in region.Producers)
            {
                if (producer.Active && producer.PostedPrice <= 0.0)
                {
                    producer.PostedPrice = region.Prices[producer.Commodity];
                    producer.LastCost = Lab.EffectiveUnitCost(producer, region.Prices);
                }
            }
            List<Producer> active = new List<Producer>();
            foreach (Producer p in region.Producers)
            {
                if (p.Active && p.CapacityPerDay > 0 && e.Commodities.ContainsKey(p.Commodity))
                {
                    active.Add(p);
                }
            }
            SortByNameThenCommodity(active);
            return active;
        }

        /// <summary><c>sorted(..., key=lambda p: (p.name, p.commodity))</c>: stable.</summary>
        private static void SortByNameThenCommodity(List<Producer> producers)
        {
            List<KeyValuePair<int, Producer>> indexed = new List<KeyValuePair<int, Producer>>(producers.Count);
            for (int i = 0; i < producers.Count; i++)
            {
                indexed.Add(new KeyValuePair<int, Producer>(i, producers[i]));
            }
            indexed.Sort(delegate (KeyValuePair<int, Producer> x, KeyValuePair<int, Producer> y)
            {
                int byName = string.CompareOrdinal(x.Value.Name, y.Value.Name);
                if (byName != 0) { return byName; }
                int byCommodity = string.CompareOrdinal(x.Value.Commodity, y.Value.Commodity);
                return byCommodity != 0 ? byCommodity : x.Key.CompareTo(y.Key);
            });
            for (int i = 0; i < producers.Count; i++)
            {
                producers[i] = indexed[i].Value;
            }
        }

        /// <summary><c>_set_capital_consumption</c>.</summary>
        private static void SetCapitalConsumption(EconomyState e, Producer producer, Region region)
        {
            double money;
            double labor;
            Lab.CapitalConsumedPerUnit(producer.Process, producer.Commodity, e.CapitalServiceLifeDays,
                e.Commodities, CapitalMoneyPerCapacity(producer.Process, region),
                CapitalLaborPerCapacity(e, producer.Process), out money, out labor);
            producer.CapitalCostPerUnit = money;
            producer.CapitalLaborPerUnit = labor;
        }

        /// <summary><c>capital_money_per_capacity</c>.</summary>
        private static double CapitalMoneyPerCapacity(Process process, Region region)
        {
            if (process.CapitalBill.Count == 0 || region == null)
            {
                return process.CapitalMoneyPerCapacity;
            }
            List<double> materials = new List<double>();
            foreach (string name in process.CapitalBill.SortedKeys())
            {
                materials.Add(process.CapitalBill[name] * region.Prices.Get(name, 0.0));
            }
            double wagePerTick = region.SubsistenceBasket.Count > 0
                ? Lab.WageRate(region) / Lab.Max(region.TicksPerWorkerDay, Epsilon)
                : 0.0;
            return process.MachinesPerCapacity * (Lab.Sum(materials) + process.CapitalConstructionLabor * wagePerTick);
        }

        /// <summary><c>capital_labor_per_capacity</c> at the committed values.</summary>
        private static double CapitalLaborPerCapacity(EconomyState e, Process process)
        {
            if (process.CapitalBill.Count == 0)
            {
                return process.CapitalLaborPerCapacity;
            }
            List<double> terms = new List<double>();
            foreach (string name in process.CapitalBill.SortedKeys())
            {
                terms.Add(process.CapitalBill[name] * e.LaborValues.Get(name, 0.0));
            }
            return process.MachinesPerCapacity * (Lab.Sum(terms) + process.CapitalConstructionLabor);
        }

        /// <summary><c>_update_wage_costs</c>: living labor at today's basket.</summary>
        private static void UpdateWageCosts(EconomyState e, Region region)
        {
            if (region.SubsistenceBasket.Count == 0)
            {
                return;
            }
            double wagePerTick = Lab.WageRate(region) / Lab.Max(region.TicksPerWorkerDay, Epsilon);
            foreach (Producer producer in region.Producers)
            {
                if (producer.Active)
                {
                    producer.WageCostPerUnit = Lab.LaborPerUnit(producer.Process, producer.Commodity, e.Commodities) * wagePerTick;
                }
            }
        }

        /// <summary><c>_quantize_employment</c> (docs/102).</summary>
        private static double QuantizeEmployment(EconomyState e, Producer producer, Region region, double runs)
        {
            double labor = producer.Process.DirectLabor;
            if (labor <= Epsilon)
            {
                return runs;
            }
            double quantum = e.ProducerEmploymentQuantum;
            double workerDays = runs * labor / region.TicksPerWorkerDay;
            double floored = Math.Floor(workerDays / quantum) * quantum;
            return floored * region.TicksPerWorkerDay / labor;
        }

        /// <summary><c>_planned_runs</c>: the order-book fixed point.</summary>
        private static Dictionary<Producer, double> PlannedRuns(EconomyState e, Region region,
            OrderedMap<double> opening, List<Producer> active, Dictionary<Producer, double> desired)
        {
            Dictionary<Producer, double> planned = new Dictionary<Producer, double>(desired);
            List<KeyValuePair<string, List<Producer>>> grouped = GroupedByCommodity(active);
            OrderedMap<double> throughput = e.Throughput[region.Name];
            for (int iteration = 0; iteration < 1000; iteration++)
            {
                OrderedMap<double> intended = new OrderedMap<double>();
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    intended[e.Commodities.KeyAt(c)] = Lab.DailyDemand(region, e.Commodities.ValueAt(c));
                }
                foreach (Producer producer in active)
                {
                    double runs = planned[producer];
                    OrderedMap<double> inputs = producer.Process.Inputs;
                    for (int i = 0; i < inputs.Count; i++)
                    {
                        string name = inputs.KeyAt(i);
                        intended[name] = intended[name] + runs * inputs.ValueAt(i);
                    }
                }
                foreach (Producer producer in active)
                {
                    double perCapacity = producer.CapacityPerDay / e.CapitalServiceLifeDays;
                    OrderedMap<double> bill = Lab.CapitalBillPerCapacity(producer.Process);
                    for (int i = 0; i < bill.Count; i++)
                    {
                        string name = bill.KeyAt(i);
                        if (intended.ContainsKey(name))
                        {
                            intended[name] = intended[name] + perCapacity * bill.ValueAt(i);
                        }
                    }
                }
                foreach (string name in region.SubsistenceBasket.SortedKeys())
                {
                    if (intended.ContainsKey(name))
                    {
                        double quantity = region.SubsistenceBasket[name];
                        if (region.HabitualScale != 1.0)
                        {
                            quantity = quantity * region.HabitualScale;
                        }
                        intended[name] = intended[name] + quantity * region.WorkerDaysDue;
                    }
                }
                OrderedMap<double> requested = new OrderedMap<double>();
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    Commodity commodity = e.Commodities.ValueAt(c);
                    string name = commodity.Name;
                    double target = throughput[name] * commodity.TargetInventoryDays;
                    double correction = e.ReplenishmentRate * (target - opening.Get(name, 0.0));
                    requested[name] = Lab.Max(0.0, intended[name] + correction);
                }
                OrderedMap<double> desiredOutput = new OrderedMap<double>();
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    desiredOutput[e.Commodities.KeyAt(c)] = 0.0;
                }
                foreach (Producer producer in active)
                {
                    double units = producer.Process.Outputs[producer.Commodity];
                    desiredOutput[producer.Commodity] = desiredOutput[producer.Commodity] + desired[producer] * units;
                }
                Dictionary<Producer, double> revised = AllocateOrders(e, region, desired, desiredOutput, requested, grouped);
                bool same = revised.Count == planned.Count;
                if (same)
                {
                    foreach (KeyValuePair<Producer, double> entry in revised)
                    {
                        double before;
                        if (!planned.TryGetValue(entry.Key, out before) || before != entry.Value)
                        {
                            same = false;
                            break;
                        }
                    }
                }
                if (same)
                {
                    return revised;
                }
                planned = revised;
            }
            throw new InvalidOperationException("production-order plan did not converge");
        }

        /// <summary><c>_grouped_by_commodity</c>: commodities sorted, producers
        /// sorted by name within a contested sector.</summary>
        private static List<KeyValuePair<string, List<Producer>>> GroupedByCommodity(List<Producer> active)
        {
            OrderedMap<List<Producer>> byCommodity = new OrderedMap<List<Producer>>();
            foreach (Producer producer in active)
            {
                byCommodity.SetDefault(producer.Commodity, new List<Producer>()).Add(producer);
            }
            List<KeyValuePair<string, List<Producer>>> grouped = new List<KeyValuePair<string, List<Producer>>>();
            foreach (string name in byCommodity.SortedKeys())
            {
                List<Producer> producers = byCommodity[name];
                if (producers.Count > 1)
                {
                    producers = new List<Producer>(producers);
                    SortByNameThenCommodity(producers);
                }
                grouped.Add(new KeyValuePair<string, List<Producer>>(name, producers));
            }
            return grouped;
        }

        /// <summary><c>_allocate_orders</c>, posted-price weighting: the
        /// order book goes to the producer asking less (docs/57).</summary>
        private static Dictionary<Producer, double> AllocateOrders(EconomyState e, Region region,
            Dictionary<Producer, double> desired, OrderedMap<double> desiredOutput,
            OrderedMap<double> requestedOutput, List<KeyValuePair<string, List<Producer>>> grouped)
        {
            double epsilonShare = e.CompetitiveShareElasticity;
            Dictionary<Producer, double> revised = new Dictionary<Producer, double>();
            foreach (KeyValuePair<string, List<Producer>> group in grouped)
            {
                string name = group.Key;
                List<Producer> producers = group.Value;
                double availableOutput = desiredOutput[name];
                if (availableOutput <= Epsilon)
                {
                    foreach (Producer p in producers) { revised[p] = 0.0; }
                    continue;
                }
                double wanted = Lab.Min(requestedOutput[name], availableOutput);
                if (wanted <= Epsilon)
                {
                    foreach (Producer p in producers) { revised[p] = 0.0; }
                    continue;
                }
                Dictionary<Producer, double> ceilings = new Dictionary<Producer, double>();
                foreach (Producer p in producers)
                {
                    ceilings[p] = desired[p] * p.Process.Outputs[p.Commodity];
                }
                Dictionary<Producer, double> weights = new Dictionary<Producer, double>();
                if (epsilonShare <= 0.0)
                {
                    foreach (Producer p in producers) { weights[p] = ceilings[p]; }
                }
                else
                {
                    Dictionary<Producer, double> costs = new Dictionary<Producer, double>();
                    double cheapest = 0.0;
                    for (int i = 0; i < producers.Count; i++)
                    {
                        Producer p = producers[i];
                        double cost = Lab.Max(p.PostedPrice, Epsilon);
                        costs[p] = cost;
                        cheapest = i == 0 ? cost : Lab.Min(cheapest, cost);
                    }
                    foreach (Producer p in producers)
                    {
                        weights[p] = ceilings[p] * Math.Pow(costs[p] / cheapest, -epsilonShare);
                    }
                }
                Dictionary<Producer, double> allotted = new Dictionary<Producer, double>();
                foreach (Producer p in producers) { allotted[p] = 0.0; }
                double remaining = wanted;
                List<Producer> open = new List<Producer>();
                foreach (Producer p in producers)
                {
                    if (ceilings[p] > Epsilon) { open.Add(p); }
                }
                for (int round = 0; round < producers.Count + 1; round++)
                {
                    if (remaining <= Epsilon || open.Count == 0)
                    {
                        break;
                    }
                    List<double> openWeights = new List<double>(open.Count);
                    foreach (Producer p in open) { openWeights.Add(weights[p]); }
                    double totalWeight = Lab.Sum(openWeights);
                    if (totalWeight <= Epsilon)
                    {
                        break;
                    }
                    HashSet<Producer> capped = new HashSet<Producer>();
                    double placed = 0.0;
                    foreach (Producer p in open)
                    {
                        double share = remaining * weights[p] / totalWeight;
                        double room = ceilings[p] - allotted[p];
                        double take = Lab.Min(share, room);
                        allotted[p] = allotted[p] + take;
                        placed += take;
                        if (room - take <= Epsilon)
                        {
                            capped.Add(p);
                        }
                    }
                    remaining -= placed;
                    if (capped.Count == 0)
                    {
                        break;
                    }
                    open = open.FindAll(delegate (Producer p) { return !capped.Contains(p); });
                }
                foreach (Producer producer in producers)
                {
                    double units = producer.Process.Outputs[producer.Commodity];
                    revised[producer] = allotted[producer] / units;
                }
            }
            return revised;
        }

        /// <summary><c>_replace_plant</c>: nothing for a process without a bill.</summary>
        private static double ReplacePlant(EconomyState e, Region region, Producer producer,
            OrderedMap<double> ration, OrderedMap<double> drawn)
        {
            OrderedMap<double> bill = Lab.CapitalBillPerCapacity(producer.Process);
            if (bill.Count == 0 || producer.CapacityPerDay <= Epsilon)
            {
                return 0.0;
            }
            throw new NotSupportedException("plant with a bill of materials is not carried (docs/141 s2)");
        }

        /// <summary><c>_pay_for_draws</c>: inputs at regional prices, to their sellers.</summary>
        private static void PayForDraws(EconomyState e, Region region, List<Producer> active,
            OrderedMap<double> ration, Dictionary<string, List<Share>> shares)
        {
            foreach (Producer producer in active)
            {
                double runs = producer.LastRuns;
                if (runs > Epsilon)
                {
                    OrderedMap<double> inputs = producer.Process.Inputs;
                    for (int i = 0; i < inputs.Count; i++)
                    {
                        string name = inputs.KeyAt(i);
                        double perRun = inputs.ValueAt(i);
                        double credited = PaySellers(e, region, name,
                            runs * perRun * region.Prices.Get(name, 0.0), shares, false, runs * perRun);
                        producer.Cash -= credited;
                        Add(e.Ledger.ProducerPurchases, region.Name, credited);
                    }
                }
                if (Lab.CapitalBillPerCapacity(producer.Process).Count > 0 && producer.CapacityPerDay > Epsilon)
                {
                    throw new NotSupportedException("plant with a bill of materials is not carried (docs/141 s2)");
                }
            }
        }

        /// <summary><c>_shed_capacity</c>: bill-free plant wears under rule two.</summary>
        private static void ShedCapacity(EconomyState e, Region region, List<Producer> active)
        {
            foreach (Producer producer in active)
            {
                if (producer.Process.CapitalBill.Count == 0)
                {
                    if (e.Accumulate)
                    {
                        WearBillFree(e, region, producer);
                    }
                    continue;
                }
                throw new NotSupportedException("plant with a bill of materials is not carried (docs/141 s2)");
            }
        }

        /// <summary><c>_wear_bill_free</c> (docs/132 s3): the day's wear
        /// replaced from the purse, paid to the fund; what it cannot pay is shed.</summary>
        private static void WearBillFree(EconomyState e, Region region, Producer producer)
        {
            double life = Lab.Max(e.CapitalServiceLifeDays, Epsilon);
            double unit = BillFreeConstructionUnit(e, producer, region);
            double due = producer.CapacityPerDay * unit / life;
            if (due <= 0.0)
            {
                return;
            }
            double paid = Lab.Min(due, Lab.Max(producer.Cash, 0.0));
            if (paid > 0.0)
            {
                producer.Cash -= paid;
                region.Cash += paid;
                Add(e.Ledger.ConstructionWages, region.Name, paid);
            }
            double lost = producer.CapacityPerDay * (1.0 - paid / due) / life;
            if (lost <= 0.0)
            {
                return;
            }
            producer.CapacityPerDay -= lost;
            Add(e.Ledger.CapacityLost, producer.Commodity, lost);
            if (producer.CapacityPerDay < 1e-9)
            {
                producer.CapacityPerDay = 0.0;
                producer.Active = false;
            }
        }

        /// <summary><c>_settle_labor</c> with purses: the wage relation (docs/17).</summary>
        private static void SettleLabor(EconomyState e, Region region, List<Producer> active,
            Dictionary<Producer, double> laborByProducer, double laborPerformed)
        {
            double workerDays;
            if (e.EmploymentQuantum > 0.0)
            {
                workerDays = Math.Floor((laborPerformed / region.TicksPerWorkerDay) / e.EmploymentQuantum)
                    * e.EmploymentQuantum;
            }
            else
            {
                workerDays = laborPerformed / region.TicksPerWorkerDay;
            }
            region.WorkerDaysEarned = workerDays;
            if (region.SubsistenceBasket.Count == 0)
            {
                return;
            }
            double wageBill = workerDays * Lab.WageRate(region);
            PayWages(e, region, active, laborByProducer, laborPerformed, wageBill);
            Add(e.Ledger.WagesPaid, region.Name, wageBill);
            Add(e.Ledger.LivingLabor, region.Name, laborPerformed);
            double necessaryPerDay = BasketLaborValue(e, region);
            double valueOfLaborPower = region.HabitualScale == 1.0 ? necessaryPerDay : necessaryPerDay * region.HabitualScale;
            Add(e.Ledger.NecessaryLabor, region.Name, workerDays * valueOfLaborPower);
            if (region.WagePremium != 0.0 || region.HabitualScale != 1.0)
            {
                Add(e.Ledger.WagePremiumPaid, region.Name, workerDays * Lab.BasketCost(region) * region.WagePremium);
                double deviation = region.HabitualScale == 1.0
                    ? necessaryPerDay * region.WagePremium
                    : necessaryPerDay * (1.0 + region.WagePremium - region.HabitualScale);
                Add(e.Ledger.WageDeviationLabor, region.Name, workerDays * deviation);
            }
        }

        /// <summary><c>basket_labor_value</c>: the basket at social values.</summary>
        private static double BasketLaborValue(EconomyState e, Region region)
        {
            List<double> terms = new List<double>();
            foreach (string name in region.SubsistenceBasket.SortedKeys())
            {
                if (e.Commodities.ContainsKey(name))
                {
                    terms.Add(region.SubsistenceBasket[name] * e.LaborValues.Get(name, 0.0));
                }
            }
            return Lab.Sum(terms);
        }

        /// <summary><c>_pay_wages</c>: the bill split by labor used; the fund
        /// tops up what a purse cannot cover (docs/55).</summary>
        private static void PayWages(EconomyState e, Region region, List<Producer> active,
            Dictionary<Producer, double> laborByProducer, double laborPerformed, double wageBill)
        {
            if (wageBill <= 0.0)
            {
                return;
            }
            double credited = 0.0;
            if (laborPerformed > Epsilon)
            {
                foreach (Producer producer in active)
                {
                    double labor;
                    laborByProducer.TryGetValue(producer, out labor);
                    if (labor <= 0.0)
                    {
                        continue;
                    }
                    double share = wageBill * labor / laborPerformed;
                    double paid = Lab.Min(share, Lab.Max(producer.Cash, 0.0));
                    if (paid <= 0.0)
                    {
                        continue;
                    }
                    producer.Cash -= paid;
                    region.WorkerCash += paid;
                    credited += paid;
                }
            }
            double residual = wageBill - credited;
            if (residual > 0.0)
            {
                if (residual > region.Cash)
                {
                    throw new InvalidOperationException("region '" + region.Name + "' cannot cover its wage bill");
                }
                region.Cash -= residual;
                region.WorkerCash += residual;
                Add(e.Ledger.FundWageSupport, region.Name, residual);
            }
        }
    }
}
