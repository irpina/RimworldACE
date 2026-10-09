using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// docs/141 slice 2: <c>wright_battery.build_ours(seed, **DOCKED)</c>,
    /// transliterated -- <c>scale.synthetic_economy</c>, the economy it
    /// builds, <c>build_ours</c>'s rescaling, and the second economy built
    /// over the same regions with the docked settings.
    /// </summary>
    public static partial class DockedDay
    {
        // wright_battery and scale constants, as the laboratory spells them.
        private const double Demand = 800.0;
        private const double BasketFraction = 0.02;
        private const double LaborPoolPerDemand = 400.0;
        private const double CashMultiplier = 0.3;
        private const double AuthoredCashMultiplier = 10.0;
        private const double PurseFloorPerDemand = 50.0;
        private const int ProducersPerCommodity = 4;
        private const double CostSpread = 1.0;
        private const double InputCostShare = 0.45;
        private const double CostShareOfPrice = 2.0 / 3.0;
        private const int Neighbours = 3;
        private const double CapacityHeadroom = 1.25;
        private const double TargetInventoryDays = 20.0;
        /// <summary><c>wright_battery.FUND_BASIS_COMMODITIES</c>: the size at
        /// which the docking calibrated the stocks against the flow.</summary>
        private const int FundBasisCommodities = 200;

        /// <summary>The docked economy for a seed, at a size.</summary>
        public static EconomyState Build(long seed, int commodities, int regions)
        {
            List<Region> built;
            List<Commodity> goods;
            List<Route> routes;
            Synthetic(seed, commodities, regions, out goods, out built, out routes);

            // The first economy: every setting at its default.
            EconomyState first = new EconomyState();
            first.ApplyConstructorDefaults();
            first.RecordHistory = false;
            Construct(first, goods, built, routes);

            // docs/145: the stocks keep the ratio to the authored flow that
            // docked at 200 commodities; exactly one there.
            Region head = built[0];
            List<double> here = new List<double>();
            for (int i = 0; i < head.BaseDailyDemand.Count; i++)
            {
                here.Add(head.BaseDailyDemand.ValueAt(i) * head.Prices[head.BaseDailyDemand.KeyAt(i)]);
            }
            double scale = Lab.Sum(here) / AuthoredValue(FundBasisCommodities);
            foreach (Region region in built)
            {
                region.LaborPool = LaborPoolPerDemand * Demand * scale;
                region.Cash *= CashMultiplier * Demand * scale;
                region.WorkerCash *= Demand * (CashMultiplier / AuthoredCashMultiplier) * scale;
                foreach (Producer producer in region.Producers)
                {
                    producer.Cash = Lab.Max(producer.Cash, PurseFloorPerDemand * Demand);
                }
            }

            EconomyState e = new EconomyState();
            e.ApplyConstructorDefaults();
            e.RecordHistory = false;
            e.ProducerCash = true;
            e.PostedPrices = true;
            e.ProducerEmploymentQuantum = 1.0;
            e.InvestmentIntervalDays = 1000000;
            e.Accumulate = true;
            e.RetentionRate = 0.5;
            e.ConstructionCostMultiplier = 20.0;
            Construct(e, goods, built, routes);

            Region opening = built[0];
            List<double> authored = new List<double>();
            for (int i = 0; i < opening.BaseDailyDemand.Count; i++)
            {
                authored.Add(opening.BaseDailyDemand.ValueAt(i) * opening.Prices[opening.BaseDailyDemand.KeyAt(i)]);
            }
            if (opening.Cash <= 0.0)
            {
                throw new InvalidOperationException(
                    "region '" + opening.Name + "' has no silver left after seeding purses");
            }
            e.FundSpendingRate = Lab.Sum(authored) / opening.Cash;
            return e;
        }

        /// <summary><c>wright_battery.authored_value</c>: the deepest
        /// commodities' demand at reference prices, in population order.</summary>
        private static double AuthoredValue(int commodities)
        {
            List<Population.Row> rows = Population.Sample(commodities);
            int deepest = int.MinValue;
            foreach (Population.Row row in rows)
            {
                deepest = Math.Max(deepest, row.Depth);
            }
            List<double> terms = new List<double>();
            foreach (Population.Row row in rows)
            {
                if (row.Depth == deepest)
                {
                    terms.Add(Demand * row.Price);
                }
            }
            return Lab.Sum(terms);
        }

        /// <summary><c>scale.synthetic_economy</c> up to the economy it
        /// constructs, at the docked arguments.</summary>
        private static void Synthetic(long seed, int commodities, int regionCount,
            out List<Commodity> goods, out List<Region> built, out List<Route> routes)
        {
            List<Population.Row> rows = Population.Sample(commodities);
            Dictionary<string, double> labor;
            Dictionary<string, double> price;
            Dictionary<string, Process> processes = BuildProcesses(rows, seed, out labor, out price);

            goods = new List<Commodity>();
            foreach (Population.Row row in rows)
            {
                Commodity good = new Commodity();
                good.Name = row.Name;
                good.ReferencePrice = row.Price;
                good.LaborValue = row.Labor;
                good.TargetInventoryDays = TargetInventoryDays;
                goods.Add(good);
            }

            int deepest = int.MinValue;
            foreach (Population.Row row in rows)
            {
                deepest = Math.Max(deepest, row.Depth);
            }
            OrderedMap<double> finalDemand = new OrderedMap<double>();
            foreach (Population.Row row in rows)
            {
                if (row.Depth == deepest)
                {
                    finalDemand[row.Name] = Demand;
                }
            }

            List<Population.Row> shallow = new List<Population.Row>();
            foreach (Population.Row row in rows)
            {
                if (row.Depth == 0)
                {
                    shallow.Add(row);
                }
            }
            if (shallow.Count == 0)
            {
                shallow = rows;
            }
            Population.Row staple = shallow[0];
            foreach (Population.Row row in shallow)
            {
                if (row.Price < staple.Price
                    || (row.Price == staple.Price && string.CompareOrdinal(row.Name, staple.Name) < 0))
                {
                    staple = row;
                }
            }
            const double ticksPerWorkerDay = 24000.0;
            double basketQuantity = Lab.Max(
                BasketFraction * ticksPerWorkerDay / Lab.Max(labor[staple.Name], 1.0), 1e-6);
            OrderedMap<double> required = RequiredWithBasket(rows, processes, finalDemand,
                staple.Name, basketQuantity, ticksPerWorkerDay);

            LabRandom spread = new LabRandom(unchecked(seed + 1));
            List<string> regionNames = new List<string>();
            for (int index = 0; index < regionCount; index++)
            {
                regionNames.Add("region_" + index.ToString("000", System.Globalization.CultureInfo.InvariantCulture));
            }
            built = new List<Region>();
            for (int index = 0; index < regionNames.Count; index++)
            {
                string regionName = regionNames[index];
                double jitter = 1.0 + 0.01 * ((index % 5) - 2);
                List<Producer> producers = new List<Producer>();
                foreach (Population.Row row in rows)
                {
                    string name = row.Name;
                    Process process = processes[name];
                    double capacity = Lab.Max(required.Get(name, 0.0) * CapacityHeadroom, 1e-6);
                    List<double> referenceTerms = new List<double>();
                    for (int i = 0; i < process.Inputs.Count; i++)
                    {
                        referenceTerms.Add(process.Inputs.ValueAt(i) * price[process.Inputs.KeyAt(i)]);
                    }
                    double referenceInputs = Lab.Sum(referenceTerms);
                    double overhead = Lab.Max(0.0, CostShareOfPrice * price[name] * jitter - referenceInputs);
                    for (int firm = 0; firm < ProducersPerCommodity; firm++)
                    {
                        double unit = LabRandom.ToDouble(spread.Next()) / 18446744073709551616.0;
                        Producer producer = new Producer();
                        producer.Name = regionName + ":" + name + "#" + firm.ToString(System.Globalization.CultureInfo.InvariantCulture);
                        producer.Commodity = name;
                        producer.CapacityPerDay = capacity / ProducersPerCommodity;
                        producer.UnitCost = overhead * (1.0 + CostSpread * (unit - 0.5));
                        producer.Process = process;
                        producers.Add(producer);
                    }
                }
                Region region = new Region();
                region.Name = regionName;
                region.Cash = 1000000.0;
                region.BaseDailyDemand = Lab.Copy(finalDemand);
                foreach (Population.Row row in rows)
                {
                    region.Prices[row.Name] = row.Price;
                }
                region.Producers = producers;
                region.SubsistenceBasket[staple.Name] = basketQuantity;
                region.TicksPerWorkerDay = ticksPerWorkerDay;
                region.WorkerCash = 100000.0;
                built.Add(region);
            }

            routes = new List<Route>();
            for (int index = 0; index < regionNames.Count; index++)
            {
                for (int step = 1; step <= Neighbours; step++)
                {
                    int other = (index + step) % regionNames.Count;
                    if (other == index)
                    {
                        continue;
                    }
                    string a = regionNames[index];
                    string b = regionNames[other];
                    if (string.CompareOrdinal(a, b) > 0)
                    {
                        string swap = a;
                        a = b;
                        b = swap;
                    }
                    bool seen = false;
                    foreach (Route route in routes)
                    {
                        if (route.A == a && route.B == b)
                        {
                            seen = true;
                            break;
                        }
                    }
                    if (seen)
                    {
                        continue;
                    }
                    Route added = new Route();
                    added.A = a;
                    added.B = b;
                    added.FreightPerUnit = 1.0;
                    added.CapacityPerDay = 25.0;
                    added.TravelDays = 4;
                    routes.Add(added);
                }
            }

            foreach (Region region in built)
            {
                foreach (Commodity good in goods)
                {
                    region.Inventory.SetDefault(good.Name, 0.0);
                }
                OrderedMap<double> throughput = Lab.ThroughputDemands(region);
                foreach (Commodity good in goods)
                {
                    region.Inventory[good.Name] = throughput[good.Name] * good.TargetInventoryDays;
                }
            }
        }

        /// <summary><c>scale.build_processes</c>: one technology per
        /// commodity, wired by depth from the seed's stream.</summary>
        private static Dictionary<string, Process> BuildProcesses(List<Population.Row> rows, long seed,
            out Dictionary<string, double> labor, out Dictionary<string, double> price)
        {
            LabRandom random = new LabRandom(seed);
            OrderedMap<List<Population.Row>> byDepth = new OrderedMap<List<Population.Row>>();
            labor = new Dictionary<string, double>(StringComparer.Ordinal);
            price = new Dictionary<string, double>(StringComparer.Ordinal);
            foreach (Population.Row row in rows)
            {
                string depthKey = row.Depth.ToString(System.Globalization.CultureInfo.InvariantCulture);
                byDepth.SetDefault(depthKey, new List<Population.Row>()).Add(row);
                labor[row.Name] = row.Labor;
                price[row.Name] = row.Price;
            }
            Dictionary<string, Process> processes = new Dictionary<string, Process>(StringComparer.Ordinal);
            foreach (Population.Row row in SortedByDepthThenName(rows))
            {
                string name = row.Name;
                List<Population.Row> pool = new List<Population.Row>();
                for (int shallower = 0; shallower < row.Depth; shallower++)
                {
                    List<Population.Row> found;
                    if (byDepth.TryGetValue(shallower.ToString(System.Globalization.CultureInfo.InvariantCulture), out found))
                    {
                        pool.AddRange(found);
                    }
                }
                OrderedMap<double> inputs = new OrderedMap<double>();
                if (pool.Count > 0)
                {
                    int count = 1 + random.Below(4);
                    double budget = InputCostShare * price[name] / count;
                    for (int draw = 0; draw < count; draw++)
                    {
                        string other = pool[random.Below(pool.Count)].Name;
                        if (other == name)
                        {
                            continue;
                        }
                        double quantity = budget / Lab.Max(price[other], 1e-9);
                        inputs[other] = inputs.Get(other, 0.0) + quantity;
                    }
                }
                List<double> carriedTerms = new List<double>();
                for (int i = 0; i < inputs.Count; i++)
                {
                    carriedTerms.Add(inputs.ValueAt(i) * labor[inputs.KeyAt(i)]);
                }
                double direct = labor[name] - Lab.Sum(carriedTerms);
                if (direct < 1.0)
                {
                    direct = 1.0;
                }
                Process process = new Process();
                process.Name = name + " production";
                process.Outputs[name] = 1.0;
                process.Inputs = inputs;
                process.DirectLabor = direct;
                processes[name] = process;
            }
            return processes;
        }

        private static List<Population.Row> SortedByDepthThenName(List<Population.Row> rows)
        {
            // A stable sort: List.Sort is not, so the index breaks ties.
            List<KeyValuePair<int, Population.Row>> keyed = new List<KeyValuePair<int, Population.Row>>();
            for (int i = 0; i < rows.Count; i++)
            {
                keyed.Add(new KeyValuePair<int, Population.Row>(i, rows[i]));
            }
            keyed.Sort((x, y) =>
            {
                int order = x.Value.Depth.CompareTo(y.Value.Depth);
                if (order == 0)
                {
                    order = string.CompareOrdinal(x.Value.Name, y.Value.Name);
                }
                return order != 0 ? order : x.Key.CompareTo(y.Key);
            });
            List<Population.Row> sorted = new List<Population.Row>();
            foreach (KeyValuePair<int, Population.Row> pair in keyed)
            {
                sorted.Add(pair.Value);
            }
            return sorted;
        }

        /// <summary><c>scale._required_output</c>: demand cascaded from the
        /// deepest commodity to the shallowest.</summary>
        private static OrderedMap<double> RequiredOutput(List<Population.Row> rows,
            Dictionary<string, Process> processes, OrderedMap<double> finalDemand)
        {
            OrderedMap<double> required = new OrderedMap<double>();
            foreach (Population.Row row in rows)
            {
                required[row.Name] = finalDemand.Get(row.Name, 0.0);
            }
            // sorted(rows, key=-depth): stable, so deepest first in row order.
            List<KeyValuePair<int, Population.Row>> keyed = new List<KeyValuePair<int, Population.Row>>();
            for (int i = 0; i < rows.Count; i++)
            {
                keyed.Add(new KeyValuePair<int, Population.Row>(i, rows[i]));
            }
            keyed.Sort((x, y) =>
            {
                int order = y.Value.Depth.CompareTo(x.Value.Depth);
                return order != 0 ? order : x.Key.CompareTo(y.Key);
            });
            foreach (KeyValuePair<int, Population.Row> pair in keyed)
            {
                string name = pair.Value.Name;
                double runs = required[name];
                if (runs <= 0.0)
                {
                    continue;
                }
                OrderedMap<double> inputs = processes[name].Inputs;
                for (int i = 0; i < inputs.Count; i++)
                {
                    string other = inputs.KeyAt(i);
                    required[other] = required.Get(other, 0.0) + runs * inputs.ValueAt(i);
                }
            }
            return required;
        }

        /// <summary><c>scale._required_with_basket</c> (docs/128): the
        /// cascade with the workforce's basket in the demand, to a fixed point.</summary>
        private static OrderedMap<double> RequiredWithBasket(List<Population.Row> rows,
            Dictionary<string, Process> processes, OrderedMap<double> finalDemand,
            string staple, double basketQuantity, double ticksPerWorkerDay)
        {
            const double tolerance = 1e-6;
            const int maxIterations = 200;
            OrderedMap<double> required = RequiredOutput(rows, processes, finalDemand);
            for (int iteration = 1; iteration <= maxIterations; iteration++)
            {
                List<double> terms = new List<double>();
                for (int i = 0; i < required.Count; i++)
                {
                    terms.Add(required.ValueAt(i) * processes[required.KeyAt(i)].DirectLabor);
                }
                double workers = Lab.Sum(terms) / ticksPerWorkerDay;
                OrderedMap<double> demand = Lab.Copy(finalDemand);
                demand[staple] = demand.Get(staple, 0.0) + workers * basketQuantity;
                double previous = required[staple];
                required = RequiredOutput(rows, processes, demand);
                if (Math.Abs(required[staple] - previous) <= tolerance * Lab.Max(previous, 1.0))
                {
                    return required;
                }
            }
            throw new InvalidOperationException("basket_in_demand did not converge");
        }

        /// <summary><c>Economy.__init__</c>'s body, for the settings already
        /// on <paramref name="e"/>, over the given goods, regions and routes.</summary>
        private static void Construct(EconomyState e, List<Commodity> goods, List<Region> regions, List<Route> routes)
        {
            e.Commodities = new OrderedMap<Commodity>();
            foreach (Commodity good in goods)
            {
                e.Commodities[good.Name] = good;
            }
            e.Regions = new OrderedMap<Region>();
            foreach (Region region in regions)
            {
                e.Regions[region.Name] = region;
            }
            e.Routes = new List<Route>(routes);
            e.Shipments = new List<Shipment>();
            e.Day = 0;
            foreach (Region region in regions)
            {
                region.CapitalServiceLifeDays = e.CapitalServiceLifeDays;
            }
            e.LaborValues = new OrderedMap<double>();
            e.RegionalLaborValues = new OrderedMap<OrderedMap<double>>();
            e.StaleLaborValues = new List<string>();
            List<double> cash = new List<double>();
            foreach (Region region in regions)
            {
                cash.Add(region.Cash + region.WorkerCash);
            }
            e.Ledger = new Ledger();
            e.Ledger.InitialCash = Lab.Sum(cash);
            e.Throughput = new OrderedMap<OrderedMap<double>>();
            e.HasDailyExtraction = false;

            e.KnownProcesses = new OrderedMap<Process>();
            e.Processes = new OrderedMap<Process>();
            foreach (Region region in regions)
            {
                foreach (Producer producer in region.Producers)
                {
                    e.KnownProcesses.SetDefault(producer.Commodity, producer.Process);
                    e.Processes.SetDefault(producer.Process.Name, producer.Process);
                }
            }

            foreach (Region region in regions)
            {
                foreach (Commodity commodity in goods)
                {
                    string name = commodity.Name;
                    region.Inventory.SetDefault(name, 0.0);
                    region.Prices.SetDefault(name, commodity.ReferencePrice);
                    region.ExpectedPrices.SetDefault(name, region.Prices[name]);
                    region.UnmetDemand.SetDefault(name, 0.0);
                    region.ConsumedTotal.SetDefault(name, 0.0);
                    region.ImportedTotal.SetDefault(name, 0.0);
                    region.ExportedTotal.SetDefault(name, 0.0);
                }
            }
            RefreshThroughput(e);
            UpdateLaborValues(e, true);
            foreach (Region region in regions)
            {
                foreach (Producer producer in region.Producers)
                {
                    SetCapitalConsumption(e, producer, region);
                }
            }
            foreach (Region region in regions)
            {
                UpdateWageCosts(e, region);
                foreach (Commodity commodity in goods)
                {
                    double cost;
                    if (SectorUnitCost(region, commodity.Name, true, out cost))
                    {
                        region.SeedUnitCost[commodity.Name] = cost;
                    }
                    region.CostRatio.SetDefault(commodity.Name, 1.0);
                }
            }
            if (e.ProducerCash)
            {
                foreach (Region region in regions)
                {
                    foreach (Producer producer in region.Producers)
                    {
                        if (!producer.Active)
                        {
                            continue;
                        }
                        producer.CashTarget = e.WorkingCapitalDays * DailyOutlay(e, producer, region);
                        double seeded = Lab.Min(Lab.Max(region.Cash, 0.0), producer.CashTarget);
                        region.Cash -= seeded;
                        producer.Cash = seeded;
                    }
                }
            }
            if (e.PostedPrices)
            {
                foreach (Region region in regions)
                {
                    foreach (Producer producer in region.Producers)
                    {
                        if (!producer.Active)
                        {
                            continue;
                        }
                        producer.PostedPrice = region.Prices[producer.Commodity];
                        producer.LastCost = Lab.EffectiveUnitCost(producer, region.Prices);
                    }
                }
            }
            if (e.Procurement)
            {
                throw new NotSupportedException("procurement is not docked");
            }
            e.OpeningInventory = new OrderedMap<double>();
            foreach (Commodity commodity in goods)
            {
                List<double> held = new List<double>();
                foreach (Region region in regions)
                {
                    held.Add(region.Inventory.Get(commodity.Name, 0.0));
                }
                // No shipments at construction: the in-transit sum is zero.
                e.OpeningInventory[commodity.Name] = Lab.Sum(held) + 0.0;
            }
        }
    }
}
