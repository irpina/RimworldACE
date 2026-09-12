using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json;
using SocialProduction.Economy.Core;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// The regional price update (docs/77) and the wage-cost refresh
    /// (docs/79), against their fixture directories.
    ///
    /// Committed rather than left in a session's scratchpad, for the
    /// reason docs/92 gives: verification that cannot be re-run is not
    /// verification, it is a memory of one.
    /// </summary>
    public static class PriceCheck
    {
        private const double RelativeTolerance = 1e-9;

        public static int Run(string priceDirectory, string wageCostDirectory)
        {
            bool within = true;
            bool exact = true;
            Console.WriteLine();
            Console.WriteLine(
                "{0,-28} {1,-12} {2,8} {3,8} {4,10}",
                "price fixture", "region", "exact", "max ulp", "max rel");
            foreach (string file in Sorted(priceDirectory, "price"))
            {
                using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(file)))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("name").GetString();
                    PriceProblem problem = ReadPriceProblem(root.GetProperty("problem"));
                    PriceSolver.UpdatePrices(problem);
                    Dictionary<string, PriceRegion> byName = new Dictionary<string, PriceRegion>();
                    foreach (PriceRegion region in problem.Regions)
                    {
                        byName[region.Name] = region;
                    }
                    foreach (JsonElement expected in root.GetProperty("expected").EnumerateArray())
                    {
                        string regionName = expected.GetProperty("region").GetString();
                        Dictionary<string, double> want = Program.ReadPairs(expected.GetProperty("prices"));
                        Program.Comparison comparison = Program.Compare(want, byName[regionName].Prices);
                        Report(name, regionName, comparison, ref within, ref exact);
                    }
                }
            }

            Console.WriteLine();
            Console.WriteLine(
                "{0,-28} {1,-12} {2,8} {3,8} {4,10}",
                "wage-cost fixture", "region", "exact", "max ulp", "max rel");
            foreach (string file in Sorted(wageCostDirectory, "wage-cost"))
            {
                using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(file)))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("name").GetString();
                    Dictionary<string, Dictionary<string, double>> got =
                        new Dictionary<string, Dictionary<string, double>>();
                    foreach (JsonElement entry in root.GetProperty("problem").GetProperty("regions").EnumerateArray())
                    {
                        WageCostProblem problem = ReadWageCostProblem(entry);
                        WageCostSolver.UpdateWageCosts(problem);
                        Dictionary<string, double> values = new Dictionary<string, double>();
                        foreach (WageCostProducer producer in problem.Producers)
                        {
                            values[producer.Name] = producer.WageCostPerUnit;
                        }
                        got[problem.RegionName] = values;
                    }
                    foreach (JsonElement expected in root.GetProperty("expected").EnumerateArray())
                    {
                        string regionName = expected.GetProperty("region").GetString();
                        Dictionary<string, double> want =
                            Program.ReadPairs(expected.GetProperty("wage_cost_per_unit"));
                        Program.Comparison comparison = Program.Compare(want, got[regionName]);
                        Report(name, regionName, comparison, ref within, ref exact);
                    }
                }
            }

            Console.WriteLine();
            Console.WriteLine(exact
                ? "every price and wage-cost fixture reproduced to the bit"
                : within
                    ? "prices within tolerance, NOT bit-exact"
                    : "prices OUTSIDE tolerance");
            return within ? (exact ? 0 : 1) : 3;
        }

        private static string[] Sorted(string directory, string what)
        {
            if (!Directory.Exists(directory))
            {
                Console.Error.WriteLine("no " + what + " fixtures in " + directory);
                return new string[0];
            }
            string[] files = Directory.GetFiles(directory, "*.json");
            Array.Sort(files, string.CompareOrdinal);
            return files;
        }

        private static void Report(
            string name, string region, Program.Comparison comparison,
            ref bool within, ref bool exact)
        {
            bool ok = comparison.MaxRelative <= RelativeTolerance;
            bool bitExact = comparison.MaxUlps == 0 && comparison.Missing == 0;
            within &= ok;
            exact &= bitExact;
            Console.WriteLine(
                "{0,-28} {1,-12} {2,8} {3,8} {4,10}{5}",
                name, region,
                comparison.Exact + "/" + comparison.Compared,
                comparison.MaxUlps,
                comparison.MaxRelative.ToString("0.0e0", CultureInfo.InvariantCulture),
                ok ? "" : "  TOLERANCE");
            if (comparison.MaxUlps > 0)
            {
                Console.WriteLine("    worst: " + comparison.Worst);
            }
        }

        private static PriceProblem ReadPriceProblem(JsonElement element)
        {
            PriceProblem problem = new PriceProblem();
            problem.CompetitivePriceIntensity =
                element.GetProperty("competitive_price_intensity").GetDouble();
            problem.UnmetDemandPricePressure =
                element.GetProperty("unmet_demand_price_pressure").GetDouble();
            foreach (JsonElement commodity in element.GetProperty("commodities").EnumerateArray())
            {
                CommoditySpec spec = new CommoditySpec();
                spec.Name = commodity.GetProperty("name").GetString();
                spec.ReferencePrice = commodity.GetProperty("reference_price").GetDouble();
                spec.TargetInventoryDays = commodity.GetProperty("target_inventory_days").GetDouble();
                spec.InventoryPriceSensitivity =
                    commodity.GetProperty("inventory_price_sensitivity").GetDouble();
                spec.MinimumPriceFactor = commodity.GetProperty("minimum_price_factor").GetDouble();
                spec.MaximumPriceFactor = commodity.GetProperty("maximum_price_factor").GetDouble();
                spec.PriceAdjustmentSpeed = commodity.GetProperty("price_adjustment_speed").GetDouble();
                problem.Commodities.Add(spec);
            }
            foreach (JsonElement entry in element.GetProperty("regions").EnumerateArray())
            {
                PriceRegion region = new PriceRegion();
                region.Name = entry.GetProperty("name").GetString();
                region.Throughput = Program.ReadPairs(entry.GetProperty("throughput"));
                region.Inventory = Program.ReadPairs(entry.GetProperty("inventory"));
                region.UnmetDemand = Program.ReadPairs(entry.GetProperty("unmet_demand"));
                region.CostRatio = Program.ReadPairs(entry.GetProperty("cost_ratio"));
                region.Prices = Program.ReadPairs(entry.GetProperty("prices"));
                problem.Regions.Add(region);
            }
            return problem;
        }

        private static WageCostProblem ReadWageCostProblem(JsonElement element)
        {
            WageCostProblem problem = new WageCostProblem();
            problem.RegionName = element.GetProperty("region").GetString();
            problem.HasBasket = element.GetProperty("has_basket").GetBoolean();
            problem.WageRate = element.GetProperty("wage_rate").GetDouble();
            problem.TicksPerWorkerDay = element.GetProperty("ticks_per_worker_day").GetDouble();
            foreach (JsonElement pair in element.GetProperty("commodity_mass").EnumerateArray())
            {
                problem.CommodityMass.Add(new Quantity(pair[0].GetString(), pair[1].GetDouble()));
            }
            foreach (JsonElement entry in element.GetProperty("producers").EnumerateArray())
            {
                WageCostProducer producer = new WageCostProducer();
                producer.Name = entry.GetProperty("name").GetString();
                producer.Commodity = entry.GetProperty("commodity").GetString();
                producer.Active = entry.GetProperty("active").GetBoolean();
                JsonElement spec = entry.GetProperty("process");
                ProcessSpec process = new ProcessSpec();
                process.Name = spec.GetProperty("name").GetString();
                foreach (JsonElement pair in spec.GetProperty("outputs").EnumerateArray())
                {
                    process.Outputs.Add(new Quantity(pair[0].GetString(), pair[1].GetDouble()));
                }
                process.DirectLabor = spec.GetProperty("direct_labor").GetDouble();
                process.Apportionment = spec.GetProperty("apportionment").GetString();
                producer.Process = process;
                producer.WageCostPerUnit = entry.GetProperty("wage_cost_per_unit").GetDouble();
                problem.Producers.Add(producer);
            }
            return problem;
        }
    }
}
