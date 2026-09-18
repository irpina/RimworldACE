using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json;
using SocialProduction.Economy.Core;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// Read every wage fixture the laboratory wrote, compute the readings
    /// and the settlement, and say how far the port is from the
    /// laboratory's answer: within tolerance, and to the bit (docs/72).
    ///
    /// The same two comparisons as the value solve's, deliberately: a port
    /// that were merely correct would pass the first, and the contract
    /// docs/54 established is the second.
    /// </summary>
    public static class WageCheck
    {
        private const double RelativeTolerance = 1e-9;

        public static int Run(string directory)
        {
            if (!Directory.Exists(directory))
            {
                Console.Error.WriteLine(
                    "no wage fixtures in " + directory
                    + "; run python -m economy_lab.wage_fixtures");
                return 2;
            }
            string[] files = Directory.GetFiles(directory, "*.json");
            Array.Sort(files, string.CompareOrdinal);
            if (files.Length == 0)
            {
                Console.Error.WriteLine(
                    "no wage fixtures in " + directory
                    + "; run python -m economy_lab.wage_fixtures");
                return 2;
            }

            Console.WriteLine();
            Console.WriteLine(
                "{0,-28} {1,-12} {2,8} {3,8} {4,10}",
                "wage fixture", "region", "exact", "max ulp", "max rel");
            bool withinTolerance = true;
            bool bitExact = true;
            foreach (string file in files)
            {
                using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(file)))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("name").GetString();
                    WageProblem problem = ReadProblem(root.GetProperty("problem"));

                    Dictionary<string, JsonElement> expectedReadings =
                        new Dictionary<string, JsonElement>();
                    foreach (JsonElement reading in root.GetProperty("readings").EnumerateArray())
                    {
                        expectedReadings[reading.GetProperty("region").GetString()] = reading;
                    }
                    Dictionary<string, JsonElement> expectedSettlements =
                        new Dictionary<string, JsonElement>();
                    foreach (JsonElement settled in root.GetProperty("settlements").EnumerateArray())
                    {
                        expectedSettlements[settled.GetProperty("region").GetString()] = settled;
                    }

                    foreach (RegionState region in problem.Regions)
                    {
                        Dictionary<string, double> expected = new Dictionary<string, double>();
                        Dictionary<string, double> actual = new Dictionary<string, double>();

                        JsonElement reading = expectedReadings[region.Name];
                        Add(expected, actual, "basket_cost",
                            reading, WageSolver.BasketCost(region));
                        Add(expected, actual, "wage_rate",
                            reading, WageSolver.WageRate(region));
                        Add(expected, actual, "basket_labor_value",
                            reading, WageSolver.BasketLaborValue(problem, region));
                        Add(expected, actual, "value_of_labor_power",
                            reading, WageSolver.ValueOfLaborPower(problem, region));
                        Add(expected, actual, "employment_rate",
                            reading, WageSolver.EmploymentRate(region));
                        Add(expected, actual, "premium_over_value",
                            reading, WageSolver.PremiumOverValue(region));

                        JsonElement settled = expectedSettlements[region.Name];
                        JsonElement inputs = settled.GetProperty("inputs");
                        List<LaborEntry> labor = new List<LaborEntry>();
                        foreach (JsonElement entry in inputs.GetProperty("labor_by_producer").EnumerateArray())
                        {
                            labor.Add(new LaborEntry(
                                entry.GetProperty("producer").GetString(),
                                entry.GetProperty("ticks").GetDouble()));
                        }
                        LedgerTotals before = ReadTotals(settled.GetProperty("before"));
                        Settlement result = WageSolver.Settle(
                            problem, region, before, labor,
                            inputs.GetProperty("labor_performed").GetDouble());

                        expected["worker_days_earned"] =
                            settled.GetProperty("worker_days_earned").GetDouble();
                        actual["worker_days_earned"] = result.WorkerDaysEarned;

                        JsonElement after = settled.GetProperty("after");
                        AddTotal(expected, actual, after, "wages_paid", result.After.WagesPaid);
                        AddTotal(expected, actual, after, "living_labor", result.After.LivingLabor);
                        AddTotal(expected, actual, after, "necessary_labor", result.After.NecessaryLabor);
                        AddTotal(expected, actual, after, "wage_premium_paid", result.After.WagePremiumPaid);
                        AddTotal(expected, actual, after, "wage_deviation_labor", result.After.WageDeviationLabor);
                        AddTotal(expected, actual, after, "cash", result.After.Cash);
                        AddTotal(expected, actual, after, "worker_cash", result.After.WorkerCash);

                        Program.Comparison comparison = Program.Compare(expected, actual);
                        bool ok = comparison.MaxRelative <= RelativeTolerance;
                        bool exact = comparison.MaxUlps == 0 && comparison.Missing == 0;
                        withinTolerance &= ok;
                        bitExact &= exact;
                        Console.WriteLine(
                            "{0,-28} {1,-12} {2,8} {3,8} {4,10}{5}",
                            name,
                            region.Name,
                            comparison.Exact + "/" + comparison.Compared,
                            comparison.MaxUlps,
                            comparison.MaxRelative.ToString("0.0e0", CultureInfo.InvariantCulture),
                            ok ? "" : "  TOLERANCE");
                        if (comparison.MaxUlps > 0)
                        {
                            Console.WriteLine("    worst: " + comparison.Worst);
                        }
                    }
                }
            }

            Console.WriteLine();
            Console.WriteLine(bitExact
                ? "every wage fixture reproduced to the bit"
                : withinTolerance
                    ? "wages within tolerance, NOT bit-exact"
                    : "wages OUTSIDE tolerance");
            return withinTolerance ? (bitExact ? 0 : 1) : 3;
        }

        private static void Add(
            Dictionary<string, double> expected,
            Dictionary<string, double> actual,
            string key,
            JsonElement reading,
            double computed)
        {
            expected[key] = reading.GetProperty(key).GetDouble();
            actual[key] = computed;
        }

        private static void AddTotal(
            Dictionary<string, double> expected,
            Dictionary<string, double> actual,
            JsonElement after,
            string key,
            double computed)
        {
            expected["after." + key] = after.GetProperty(key).GetDouble();
            actual["after." + key] = computed;
        }

        private static LedgerTotals ReadTotals(JsonElement element)
        {
            LedgerTotals totals = new LedgerTotals();
            totals.WagesPaid = element.GetProperty("wages_paid").GetDouble();
            totals.LivingLabor = element.GetProperty("living_labor").GetDouble();
            totals.NecessaryLabor = element.GetProperty("necessary_labor").GetDouble();
            totals.WagePremiumPaid = element.GetProperty("wage_premium_paid").GetDouble();
            totals.WageDeviationLabor = element.GetProperty("wage_deviation_labor").GetDouble();
            totals.Cash = element.GetProperty("cash").GetDouble();
            totals.WorkerCash = element.GetProperty("worker_cash").GetDouble();
            return totals;
        }

        private static WageProblem ReadProblem(JsonElement element)
        {
            WageProblem problem = new WageProblem();
            problem.EmploymentQuantum = element.GetProperty("employment_quantum").GetDouble();
            foreach (JsonElement commodity in element.GetProperty("commodities").EnumerateArray())
            {
                problem.Commodities.Add(commodity.GetString());
            }
            problem.LaborValues = ReadQuantities(element.GetProperty("labor_values"));
            foreach (JsonElement entry in element.GetProperty("regions").EnumerateArray())
            {
                RegionState region = new RegionState();
                region.Name = entry.GetProperty("name").GetString();
                region.SubsistenceBasket = ReadQuantities(entry.GetProperty("subsistence_basket"));
                region.Prices = ReadQuantities(entry.GetProperty("prices"));
                region.WagePremium = entry.GetProperty("wage_premium").GetDouble();
                region.HabitualScale = entry.GetProperty("habitual_scale").GetDouble();
                JsonElement pool = entry.GetProperty("labor_pool");
                region.LaborPool = pool.ValueKind == JsonValueKind.Null
                    ? (double?)null
                    : pool.GetDouble();
                region.WorkerDaysEarned = entry.GetProperty("worker_days_earned").GetDouble();
                region.TicksPerWorkerDay = entry.GetProperty("ticks_per_worker_day").GetDouble();
                region.Cash = entry.GetProperty("cash").GetDouble();
                region.WorkerCash = entry.GetProperty("worker_cash").GetDouble();
                problem.Regions.Add(region);
            }
            return problem;
        }

        private static List<Quantity> ReadQuantities(JsonElement pairs)
        {
            List<Quantity> quantities = new List<Quantity>();
            foreach (JsonElement pair in pairs.EnumerateArray())
            {
                quantities.Add(new Quantity(pair[0].GetString(), pair[1].GetDouble()));
            }
            return quantities;
        }
    }
}
