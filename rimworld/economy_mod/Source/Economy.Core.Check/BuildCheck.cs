using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text.Json;
using SocialProduction.Economy.Core.Model;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// docs/141 slice 2: the port builds the docked economy from a seed and
    /// a size, and must arrive at the laboratory's start state to the bit.
    /// </summary>
    public static class BuildCheck
    {
        public static int Run(string directory)
        {
            Console.WriteLine();
            Console.WriteLine("the docked generator (docs/141 slice 2)");
            string[] files = Directory.Exists(directory) ? Directory.GetFiles(directory, "*.json.gz") : new string[0];
            Array.Sort(files, string.CompareOrdinal);
            if (files.Length == 0)
            {
                Console.Error.WriteLine("no run fixtures in " + directory + "; run python3.12 -m economy_lab.run_fixtures");
                return 2;
            }
            int failures = Rounding();
            bool controlled = false;
            foreach (string file in files)
            {
                string text;
                using (FileStream raw = File.OpenRead(file))
                using (GZipStream gzip = new GZipStream(raw, CompressionMode.Decompress))
                using (StreamReader reader = new StreamReader(gzip))
                {
                    text = reader.ReadToEnd();
                }
                using (JsonDocument document = JsonDocument.Parse(text))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("case").GetString();
                    long seed = root.GetProperty("seed").GetInt64();
                    int regions = root.GetProperty("regions").GetInt32();
                    int commodities = root.GetProperty("commodities").GetInt32();
                    List<string> differences;
                    Stopwatch clock = Stopwatch.StartNew();
                    try
                    {
                        EconomyState built = DockedDay.Build(seed, commodities, regions);
                        clock.Stop();
                        differences = StateCompare.Differences(root.GetProperty("start").GetRawText(), StateJson.Write(built), 5);
                    }
                    catch (Exception failure)
                    {
                        clock.Stop();
                        differences = new List<string> { failure.GetType().Name + ": " + failure.Message };
                    }
                    Console.WriteLine("  " + (differences.Count == 0 ? "PASS " : "FAIL ") + name
                        + ": seed " + seed + ", " + regions + " regions, " + commodities + " commodities, built in "
                        + clock.Elapsed.TotalMilliseconds.ToString("0") + " ms");
                    foreach (string difference in differences)
                    {
                        Console.WriteLine("       " + difference);
                    }
                    if (differences.Count > 0)
                    {
                        failures++;
                    }
                    else if (!controlled)
                    {
                        // Negative control: the next seed must not pass.
                        controlled = true;
                        EconomyState other = DockedDay.Build(seed + 1, commodities, regions);
                        bool caught = StateCompare.Differences(root.GetProperty("start").GetRawText(), StateJson.Write(other), 1).Count > 0;
                        Console.WriteLine("  " + (caught ? "PASS " : "FAIL ") + "control: seed " + (seed + 1) + " is told apart from " + name);
                        if (!caught)
                        {
                            failures++;
                        }
                    }
                }
            }
            Console.WriteLine(failures == 0
                ? "every start state is built to the bit from its seed"
                : failures + " start state(s) differ");
            return failures == 0 ? 0 : 1;
        }

        /// <summary>Python's <c>float(int)</c> rounds ties to even; these are
        /// the cases a once-rounding conversion and a twice-rounding one split on.</summary>
        private static int Rounding()
        {
            ulong[] values = { (1UL << 53) + 1, (1UL << 53) + 3, (1UL << 63) + (1UL << 10), (1UL << 63) + (1UL << 10) + 1,
                               ulong.MaxValue, (1UL << 53) - 1 };
            double[] expected = { 9007199254740992.0, 9007199254740996.0, 9223372036854775808.0, 9223372036854777856.0,
                                  18446744073709551616.0, 9007199254740991.0 };
            int failures = 0;
            for (int i = 0; i < values.Length; i++)
            {
                double got = LabRandom.ToDouble(values[i]);
                if (BitConverter.DoubleToInt64Bits(got) != BitConverter.DoubleToInt64Bits(expected[i]))
                {
                    Console.WriteLine("  FAIL rounding " + values[i] + ": " + got.ToString("R"));
                    failures++;
                }
            }
            Console.WriteLine("  " + (failures == 0 ? "PASS " : "FAIL ") + "integer to double rounds once, ties to even");
            return failures;
        }
    }
}
