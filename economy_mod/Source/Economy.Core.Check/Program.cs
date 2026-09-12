using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text.Json;
using SocialProduction.Economy.Core;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// Read every fixture the laboratory wrote, solve it, and say how far the
    /// port is from the laboratory's answer: within tolerance, and to the bit.
    /// </summary>
    public static class Program
    {
        private const double RelativeTolerance = 1e-9;

        public static int Main(string[] args)
        {
            string directory = args.Length > 0
                ? args[0]
                : Path.Combine(FindRepositoryRoot(), "economy_mod", "Source", "Fixtures", "labor_values");
            string[] files = Directory.GetFiles(directory, "*.json");
            Array.Sort(files, string.CompareOrdinal);
            if (files.Length == 0)
            {
                Console.Error.WriteLine("no fixtures in " + directory + "; run python -m economy_lab.fixtures");
                return 2;
            }

            Console.WriteLine(
                "{0,-28} {1,-5} {2,5} {3,5} {4,6} {5,8} {6,12} {7,10}",
                "fixture", "case", "goods", "iters", "exact", "max ulp", "max rel", "ms");
            bool withinTolerance = true;
            bool bitExact = true;
            foreach (string file in files)
            {
                using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(file)))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("name").GetString();
                    LaborValueProblem problem = ReadProblem(root.GetProperty("problem"));
                    foreach (JsonElement testCase in root.GetProperty("cases").EnumerateArray())
                    {
                        string label = testCase.GetProperty("label").GetString();
                        Dictionary<string, double> initial = ReadPairs(testCase.GetProperty("initial"));
                        JsonElement expected = testCase.GetProperty("expected");

                        Stopwatch clock = Stopwatch.StartNew();
                        LaborValueSolution solution = LaborValueSolver.Solve(problem, initial);
                        clock.Stop();

                        Comparison social = Compare(ReadPairs(expected.GetProperty("labor_values")), solution.Values);
                        Comparison regional = new Comparison();
                        foreach (JsonProperty region in expected.GetProperty("regional_labor_values").EnumerateObject())
                        {
                            Dictionary<string, double> actual;
                            if (!solution.RegionalValues.TryGetValue(region.Name, out actual))
                            {
                                actual = new Dictionary<string, double>();
                            }
                            regional.Merge(Compare(ReadPairs(region.Value), actual));
                        }
                        List<string> expectedStale = new List<string>();
                        foreach (JsonElement stale in expected.GetProperty("stale").EnumerateArray())
                        {
                            expectedStale.Add(stale.GetString());
                        }
                        bool staleAgrees = string.Join(",", expectedStale) == string.Join(",", solution.Stale);

                        Comparison all = new Comparison();
                        all.Merge(social);
                        all.Merge(regional);
                        bool ok = all.MaxRelative <= RelativeTolerance && staleAgrees;
                        bool exact = all.MaxUlps == 0 && all.Missing == 0 && staleAgrees;
                        withinTolerance &= ok;
                        bitExact &= exact;
                        Console.WriteLine(
                            "{0,-28} {1,-5} {2,5} {3,5} {4,6} {5,8} {6,12} {7,10:F2}{8}{9}",
                            name,
                            label,
                            solution.Values.Count,
                            solution.Iterations,
                            all.Exact + "/" + all.Compared,
                            all.MaxUlps,
                            all.MaxRelative.ToString("0.0e0", CultureInfo.InvariantCulture),
                            clock.Elapsed.TotalMilliseconds,
                            ok ? "" : "  TOLERANCE",
                            staleAgrees ? "" : "  STALE");
                        if (all.MaxUlps > 0)
                        {
                            Console.WriteLine("    worst: " + all.Worst);
                        }
                    }
                }
            }
            Console.WriteLine();
            Console.WriteLine(bitExact
                ? "every value-solve fixture reproduced to the bit"
                : withinTolerance
                    ? "value solve within tolerance, NOT bit-exact"
                    : "value solve OUTSIDE tolerance");

            // The wage relation (docs/72), against its own fixture set.
            string wageDirectory = args.Length > 1
                ? args[1]
                : Path.Combine(FindRepositoryRoot(), "economy_mod", "Source", "Fixtures", "wages");
            int wageCode = WageCheck.Run(wageDirectory);

            // The bargaining rules (docs/74), against their own fixtures.
            string bargainingDirectory = args.Length > 2
                ? args[2]
                : Path.Combine(FindRepositoryRoot(), "economy_mod", "Source", "Fixtures", "bargaining");
            int bargainingCode = BargainingCheck.Run(bargainingDirectory);

            int valueCode = withinTolerance ? (bitExact ? 0 : 1) : 3;
            if (valueCode != 0)
            {
                return valueCode;
            }
            return wageCode != 0 ? wageCode : bargainingCode;
        }

        internal sealed class Comparison
        {
            public int Compared;
            public int Exact;
            public int Missing;
            public long MaxUlps;
            public double MaxRelative;
            public string Worst = "";

            public void Merge(Comparison other)
            {
                Compared += other.Compared;
                Exact += other.Exact;
                Missing += other.Missing;
                if (other.MaxUlps > MaxUlps)
                {
                    MaxUlps = other.MaxUlps;
                    Worst = other.Worst;
                }
                if (other.MaxRelative > MaxRelative)
                {
                    MaxRelative = other.MaxRelative;
                }
            }
        }

        internal static Comparison Compare(Dictionary<string, double> expected, Dictionary<string, double> actual)
        {
            Comparison result = new Comparison();
            foreach (KeyValuePair<string, double> entry in expected)
            {
                double value;
                if (!actual.TryGetValue(entry.Key, out value))
                {
                    result.Missing++;
                    result.MaxRelative = double.PositiveInfinity;
                    continue;
                }
                result.Compared++;
                long ulps = Ulps(entry.Value, value);
                if (ulps == 0)
                {
                    result.Exact++;
                }
                if (ulps > result.MaxUlps)
                {
                    result.MaxUlps = ulps;
                    result.Worst = entry.Key + " expected " + entry.Value.ToString("R", CultureInfo.InvariantCulture)
                        + " got " + value.ToString("R", CultureInfo.InvariantCulture);
                }
                double scale = Math.Max(Math.Abs(entry.Value), 1e-300);
                double relative = Math.Abs(value - entry.Value) / scale;
                if (relative > result.MaxRelative)
                {
                    result.MaxRelative = relative;
                }
            }
            if (actual.Count != expected.Count)
            {
                result.Missing += Math.Abs(actual.Count - expected.Count);
            }
            return result;
        }

        internal static long Ulps(double a, double b)
        {
            if (a == b)
            {
                return 0;
            }
            long x = BitConverter.DoubleToInt64Bits(a);
            long y = BitConverter.DoubleToInt64Bits(b);
            if ((x < 0) != (y < 0))
            {
                return long.MaxValue;
            }
            return Math.Abs(x - y);
        }

        private static LaborValueProblem ReadProblem(JsonElement element)
        {
            LaborValueProblem problem = new LaborValueProblem();
            problem.Tolerance = element.GetProperty("tolerance").GetDouble();
            problem.MaxIterations = element.GetProperty("max_iterations").GetInt32();
            problem.ServiceLifeDays = element.GetProperty("service_life_days").GetDouble();
            problem.Commodities = ReadQuantities(element.GetProperty("commodities"));
            foreach (JsonElement region in element.GetProperty("regions").EnumerateArray())
            {
                problem.Regions.Add(region.GetString());
            }
            foreach (JsonElement entry in element.GetProperty("contributors").EnumerateArray())
            {
                JsonElement spec = entry.GetProperty("process");
                ProcessSpec process = new ProcessSpec();
                process.Name = spec.GetProperty("name").GetString();
                process.Outputs = ReadQuantities(spec.GetProperty("outputs"));
                process.Inputs = ReadQuantities(spec.GetProperty("inputs"));
                process.DirectLabor = spec.GetProperty("direct_labor").GetDouble();
                process.Apportionment = spec.GetProperty("apportionment").GetString();
                process.CapitalLaborPerCapacity = spec.GetProperty("capital_labor_per_capacity").GetDouble();
                process.CapitalBill = ReadQuantities(spec.GetProperty("capital_bill"));
                process.CapitalConstructionLabor = spec.GetProperty("capital_construction_labor").GetDouble();
                process.MachinesPerCapacity = spec.GetProperty("machines_per_capacity").GetDouble();
                Contributor contributor = new Contributor();
                contributor.Region = entry.GetProperty("region").GetString();
                contributor.Producer = entry.GetProperty("producer").GetString();
                contributor.Runs = entry.GetProperty("runs").GetDouble();
                contributor.Process = process;
                problem.Contributors.Add(contributor);
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

        internal static Dictionary<string, double> ReadPairs(JsonElement pairs)
        {
            Dictionary<string, double> values = new Dictionary<string, double>();
            foreach (JsonElement pair in pairs.EnumerateArray())
            {
                values[pair[0].GetString()] = pair[1].GetDouble();
            }
            return values;
        }

        internal static string FindRepositoryRoot()
        {
            string directory = AppContext.BaseDirectory;
            while (directory != null && !File.Exists(Path.Combine(directory, "HANDOFF.md")))
            {
                directory = Path.GetDirectoryName(directory);
            }
            return directory ?? Directory.GetCurrentDirectory();
        }
    }
}
