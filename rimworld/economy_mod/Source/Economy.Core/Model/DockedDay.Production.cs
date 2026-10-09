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

        /// <summary><c>_planned_runs</c>: the order-book fixed point.
        ///
        /// Transliterated, then arranged for speed without moving a bit:
        /// everything the laboratory recomputes on each pass that does not
        /// depend on the plan -- each good's own demand, the plant and
        /// basket draws, the stock correction, the desired output, and in
        /// <c>_allocate_orders</c> each producer's ceiling and cost weight --
        /// is computed once, and the dicts are arrays indexed by commodity.
        /// Every floating-point operation that remains happens in the
        /// laboratory's order on the laboratory's operands.</summary>
        private static Dictionary<Producer, double> PlannedRuns(EconomyState e, Region region,
            OrderedMap<double> opening, List<Producer> active, Dictionary<Producer, double> desired)
        {
            int goods = e.Commodities.Count;
            Dictionary<string, int> index = new Dictionary<string, int>(goods, System.StringComparer.Ordinal);
            for (int c = 0; c < goods; c++)
            {
                index[e.Commodities.KeyAt(c)] = c;
            }
            Dictionary<Producer, int> slot = new Dictionary<Producer, int>(active.Count);
            for (int a = 0; a < active.Count; a++)
            {
                slot[active[a]] = a;
            }

            // Plan-independent terms, in the order the laboratory adds them.
            double[] ownDemand = new double[goods];
            for (int c = 0; c < goods; c++)
            {
                ownDemand[c] = Lab.DailyDemand(region, e.Commodities.ValueAt(c));
            }
            int[][] inputIndex = new int[active.Count][];
            double[][] inputQuantity = new double[active.Count][];
            for (int a = 0; a < active.Count; a++)
            {
                OrderedMap<double> inputs = active[a].Process.Inputs;
                inputIndex[a] = new int[inputs.Count];
                inputQuantity[a] = new double[inputs.Count];
                for (int i = 0; i < inputs.Count; i++)
                {
                    inputIndex[a][i] = index[inputs.KeyAt(i)];
                    inputQuantity[a][i] = inputs.ValueAt(i);
                }
            }
            List<int> lateIndex = new List<int>();
            List<double> lateAmount = new List<double>();
            foreach (Producer producer in active)
            {
                double perCapacity = producer.CapacityPerDay / e.CapitalServiceLifeDays;
                OrderedMap<double> bill = Lab.CapitalBillPerCapacity(producer.Process);
                for (int i = 0; i < bill.Count; i++)
                {
                    int c;
                    if (index.TryGetValue(bill.KeyAt(i), out c))
                    {
                        lateIndex.Add(c);
                        lateAmount.Add(perCapacity * bill.ValueAt(i));
                    }
                }
            }
            foreach (string name in region.SubsistenceBasket.SortedKeys())
            {
                int c;
                if (index.TryGetValue(name, out c))
                {
                    double quantity = region.SubsistenceBasket[name];
                    if (region.HabitualScale != 1.0)
                    {
                        quantity = quantity * region.HabitualScale;
                    }
                    lateIndex.Add(c);
                    lateAmount.Add(quantity * region.WorkerDaysDue);
                }
            }
            OrderedMap<double> throughput = e.Throughput[region.Name];
            double[] correction = new double[goods];
            for (int c = 0; c < goods; c++)
            {
                Commodity commodity = e.Commodities.ValueAt(c);
                double target = throughput[commodity.Name] * commodity.TargetInventoryDays;
                correction[c] = e.ReplenishmentRate * (target - opening.Get(commodity.Name, 0.0));
            }
            double[] desiredOutput = new double[goods];
            foreach (Producer producer in active)
            {
                int c = index[producer.Commodity];
                desiredOutput[c] = desiredOutput[c] + desired[producer] * producer.Process.Outputs[producer.Commodity];
            }
            List<OrderGroup> groups = OrderGroups(e, active, desired, desiredOutput, index, slot);

            double[] planned = new double[active.Count];
            for (int a = 0; a < active.Count; a++)
            {
                planned[a] = desired[active[a]];
            }
            double[] intended = new double[goods];
            double[] requested = new double[goods];
            for (int iteration = 0; iteration < 1000; iteration++)
            {
                Array.Copy(ownDemand, intended, goods);
                for (int a = 0; a < active.Count; a++)
                {
                    double runs = planned[a];
                    int[] at = inputIndex[a];
                    double[] quantity = inputQuantity[a];
                    for (int i = 0; i < at.Length; i++)
                    {
                        intended[at[i]] = intended[at[i]] + runs * quantity[i];
                    }
                }
                for (int i = 0; i < lateIndex.Count; i++)
                {
                    intended[lateIndex[i]] = intended[lateIndex[i]] + lateAmount[i];
                }
                for (int c = 0; c < goods; c++)
                {
                    requested[c] = Lab.Max(0.0, intended[c] + correction[c]);
                }
                double[] revised = AllocateOrders(groups, requested, active.Count);
                bool same = true;
                for (int a = 0; a < active.Count; a++)
                {
                    if (planned[a] != revised[a])
                    {
                        same = false;
                        break;
                    }
                }
                if (same)
                {
                    Dictionary<Producer, double> result = new Dictionary<Producer, double>(active.Count);
                    for (int a = 0; a < active.Count; a++)
                    {
                        result[active[a]] = revised[a];
                    }
                    return result;
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

        /// <summary>One contested sector of <c>_allocate_orders</c>, with
        /// what does not change between passes of the fixed point.</summary>
        private sealed class OrderGroup
        {
            public int Commodity;
            public int[] Slots;
            public double[] Units;
            /// <summary>Null where the sector has no output to place: every
            /// producer gets nothing, whatever is requested.</summary>
            public double[] Ceilings;
            public double[] Weights;
            public double AvailableOutput;
        }

        private static List<OrderGroup> OrderGroups(EconomyState e, List<Producer> active,
            Dictionary<Producer, double> desired, double[] desiredOutput,
            Dictionary<string, int> index, Dictionary<Producer, int> slot)
        {
            double epsilonShare = e.CompetitiveShareElasticity;
            List<OrderGroup> groups = new List<OrderGroup>();
            foreach (KeyValuePair<string, List<Producer>> entry in GroupedByCommodity(active))
            {
                List<Producer> producers = entry.Value;
                OrderGroup group = new OrderGroup();
                group.Commodity = index[entry.Key];
                group.Slots = new int[producers.Count];
                group.Units = new double[producers.Count];
                for (int i = 0; i < producers.Count; i++)
                {
                    group.Slots[i] = slot[producers[i]];
                    group.Units[i] = producers[i].Process.Outputs[producers[i].Commodity];
                }
                group.AvailableOutput = desiredOutput[group.Commodity];
                if (group.AvailableOutput > Epsilon)
                {
                    group.Ceilings = new double[producers.Count];
                    for (int i = 0; i < producers.Count; i++)
                    {
                        group.Ceilings[i] = desired[producers[i]] * producers[i].Process.Outputs[producers[i].Commodity];
                    }
                    if (epsilonShare <= 0.0)
                    {
                        group.Weights = group.Ceilings;
                    }
                    else
                    {
                        double[] costs = new double[producers.Count];
                        double cheapest = 0.0;
                        for (int i = 0; i < producers.Count; i++)
                        {
                            costs[i] = Lab.Max(producers[i].PostedPrice, Epsilon);
                            cheapest = i == 0 ? costs[i] : Lab.Min(cheapest, costs[i]);
                        }
                        group.Weights = new double[producers.Count];
                        for (int i = 0; i < producers.Count; i++)
                        {
                            group.Weights[i] = group.Ceilings[i] * Math.Pow(costs[i] / cheapest, -epsilonShare);
                        }
                    }
                }
                groups.Add(group);
            }
            return groups;
        }

        /// <summary><c>_allocate_orders</c>, posted-price weighting: the
        /// order book goes to the producer asking less (docs/57).</summary>
        private static double[] AllocateOrders(List<OrderGroup> groups, double[] requestedOutput, int count)
        {
            double[] revised = new double[count];
            List<int> open = new List<int>();
            List<int> still = new List<int>();
            List<double> openWeights = new List<double>();
            foreach (OrderGroup group in groups)
            {
                int n = group.Slots.Length;
                if (group.Ceilings == null)
                {
                    continue; // revised is already zero
                }
                double wanted = Lab.Min(requestedOutput[group.Commodity], group.AvailableOutput);
                if (wanted <= Epsilon)
                {
                    continue;
                }
                double[] ceilings = group.Ceilings;
                double[] weights = group.Weights;
                double[] allotted = new double[n];
                double remaining = wanted;
                open.Clear();
                for (int i = 0; i < n; i++)
                {
                    if (ceilings[i] > Epsilon) { open.Add(i); }
                }
                for (int round = 0; round < n + 1; round++)
                {
                    if (remaining <= Epsilon || open.Count == 0)
                    {
                        break;
                    }
                    openWeights.Clear();
                    foreach (int i in open) { openWeights.Add(weights[i]); }
                    double totalWeight = Lab.Sum(openWeights);
                    if (totalWeight <= Epsilon)
                    {
                        break;
                    }
                    still.Clear();
                    bool anyCapped = false;
                    double placed = 0.0;
                    foreach (int i in open)
                    {
                        double share = remaining * weights[i] / totalWeight;
                        double room = ceilings[i] - allotted[i];
                        double take = Lab.Min(share, room);
                        allotted[i] = allotted[i] + take;
                        placed += take;
                        if (room - take <= Epsilon)
                        {
                            anyCapped = true;
                        }
                        else
                        {
                            still.Add(i);
                        }
                    }
                    remaining -= placed;
                    if (!anyCapped)
                    {
                        break;
                    }
                    List<int> swap = open;
                    open = still;
                    still = swap;
                }
                for (int i = 0; i < n; i++)
                {
                    revised[group.Slots[i]] = allotted[i] / group.Units[i];
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
