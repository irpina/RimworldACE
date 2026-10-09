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
    /// docs/141 slice 8: whole days, back to back, from the laboratory's
    /// start state to its state many days on, to the bit; and the time a
    /// day takes, for prediction 10.
    /// </summary>
    public static class RunCheck
    {
        public static int Run(string directory)
        {
            Console.WriteLine();
            Console.WriteLine("whole runs of the docked day (docs/141 slice 8)");
            string[] files = Directory.Exists(directory) ? Directory.GetFiles(directory, "*.json.gz") : new string[0];
            Array.Sort(files, string.CompareOrdinal);
            if (files.Length == 0)
            {
                Console.Error.WriteLine("no run fixtures in " + directory + "; run python3.12 -m economy_lab.run_fixtures");
                return 2;
            }
            int failures = 0;
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
                    int days = root.GetProperty("days").GetInt32();
                    EconomyState state = StateJson.Read(root.GetProperty("start"));
                    int producers = 0;
                    for (int r = 0; r < state.Regions.Count; r++)
                    {
                        producers += state.Regions.ValueAt(r).Producers.Count;
                    }
                    List<string> differences;
                    Stopwatch clock = Stopwatch.StartNew();
                    try
                    {
                        for (int d = 0; d < days; d++)
                        {
                            DockedDay.Run(state);
                        }
                        clock.Stop();
                        differences = StateCompare.Differences(root.GetProperty("end").GetRawText(), StateJson.Write(state), 5);
                    }
                    catch (Exception failure)
                    {
                        clock.Stop();
                        differences = new List<string> { failure.GetType().Name + " on day " + state.Day + ": " + failure.Message };
                    }
                    double perDay = clock.Elapsed.TotalMilliseconds / days;
                    Console.WriteLine("  " + (differences.Count == 0 ? "PASS " : "FAIL ") + name + ": "
                        + days + " days, " + producers + " producers, "
                        + perDay.ToString("0.00") + " ms a day");
                    foreach (string difference in differences)
                    {
                        Console.WriteLine("       " + difference);
                    }
                    if (differences.Count > 0)
                    {
                        failures++;
                    }
                }
            }
            Console.WriteLine(failures == 0
                ? "every run reproduces the laboratory to the bit, day after day"
                : failures + " run(s) did NOT reproduce the laboratory");
            return failures == 0 ? 0 : 7;
        }
    }
}
