using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json;
using SocialProduction.Economy.Core;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// Read every bargaining fixture, run the rules step after step, and
    /// compare the state after *every* step -- not only the last (docs/74
    /// section 2).  These rules accumulate, so a drift shows up on the
    /// step it begins rather than at the end, and a check of the final
    /// value alone would report one failure for sixty days of error.
    /// </summary>
    public static class BargainingCheck
    {
        private const double RelativeTolerance = 1e-9;

        public static int Run(string directory)
        {
            if (!Directory.Exists(directory))
            {
                Console.Error.WriteLine(
                    "no bargaining fixtures in " + directory
                    + "; run python -m economy_lab.bargaining_fixtures");
                return 2;
            }
            string[] files = Directory.GetFiles(directory, "*.json");
            Array.Sort(files, string.CompareOrdinal);
            if (files.Length == 0)
            {
                Console.Error.WriteLine(
                    "no bargaining fixtures in " + directory
                    + "; run python -m economy_lab.bargaining_fixtures");
                return 2;
            }

            Console.WriteLine();
            Console.WriteLine(
                "{0,-28} {1,-12} {2,8} {3,8} {4,10} {5,8}",
                "bargaining fixture", "region", "exact", "max ulp", "max rel", "1st bad");
            bool withinTolerance = true;
            bool bitExact = true;
            foreach (string file in files)
            {
                using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(file)))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("name").GetString();
                    BargainingProblem problem = ReadProblem(root.GetProperty("problem"));
                    Dictionary<string, BargainingState> byName =
                        new Dictionary<string, BargainingState>();
                    foreach (BargainingState region in problem.Regions)
                    {
                        byName[region.Name] = region;
                    }

                    foreach (JsonElement sequence in root.GetProperty("sequences").EnumerateArray())
                    {
                        string regionName = sequence.GetProperty("region").GetString();
                        BargainingState region = byName[regionName];
                        Dictionary<string, double> expected = new Dictionary<string, double>();
                        Dictionary<string, double> actual = new Dictionary<string, double>();
                        int step = 0;
                        int firstBad = -1;
                        foreach (JsonElement expectedStep in sequence.GetProperty("steps").EnumerateArray())
                        {
                            BargainingSolver.Step(problem, region);
                            double expectedPremium = expectedStep.GetProperty("wage_premium").GetDouble();
                            double expectedScale = expectedStep.GetProperty("habitual_scale").GetDouble();
                            expected["step" + step + ".wage_premium"] = expectedPremium;
                            actual["step" + step + ".wage_premium"] = region.WagePremium;
                            expected["step" + step + ".habitual_scale"] = expectedScale;
                            actual["step" + step + ".habitual_scale"] = region.HabitualScale;
                            if (firstBad < 0
                                && (Program.Ulps(expectedPremium, region.WagePremium) != 0
                                    || Program.Ulps(expectedScale, region.HabitualScale) != 0))
                            {
                                firstBad = step;
                            }
                            step++;
                        }

                        Program.Comparison comparison = Program.Compare(expected, actual);
                        bool ok = comparison.MaxRelative <= RelativeTolerance;
                        bool exact = comparison.MaxUlps == 0 && comparison.Missing == 0;
                        withinTolerance &= ok;
                        bitExact &= exact;
                        Console.WriteLine(
                            "{0,-28} {1,-12} {2,8} {3,8} {4,10} {5,8}{6}",
                            name,
                            regionName,
                            comparison.Exact + "/" + comparison.Compared,
                            comparison.MaxUlps,
                            comparison.MaxRelative.ToString("0.0e0", CultureInfo.InvariantCulture),
                            firstBad < 0 ? "-" : firstBad.ToString(CultureInfo.InvariantCulture),
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
                ? "every bargaining fixture reproduced to the bit, on every step"
                : withinTolerance
                    ? "bargaining within tolerance, NOT bit-exact"
                    : "bargaining OUTSIDE tolerance");
            return withinTolerance ? (bitExact ? 0 : 1) : 3;
        }

        private static BargainingProblem ReadProblem(JsonElement element)
        {
            BargainingProblem problem = new BargainingProblem();
            problem.WageBargainingStrength =
                element.GetProperty("wage_bargaining_strength").GetDouble();
            problem.WageBargainingSpeed =
                element.GetProperty("wage_bargaining_speed").GetDouble();
            problem.HabituationSpeed = element.GetProperty("habituation_speed").GetDouble();
            foreach (JsonElement entry in element.GetProperty("regions").EnumerateArray())
            {
                BargainingState region = new BargainingState();
                region.Name = entry.GetProperty("name").GetString();
                region.HasBasket = entry.GetProperty("has_basket").GetBoolean();
                region.EmploymentRate = entry.GetProperty("employment_rate").GetDouble();
                region.ReferenceEmploymentRate =
                    entry.GetProperty("reference_employment_rate").GetDouble();
                region.WagePremium = entry.GetProperty("wage_premium").GetDouble();
                region.HabitualScale = entry.GetProperty("habitual_scale").GetDouble();
                problem.Regions.Add(region);
            }
            return problem;
        }
    }
}
