using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Text.Json;
using SocialProduction.Economy.Core.Model;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// docs/141 §4: each ported phase, run on the laboratory's state before
    /// it, must produce the laboratory's state after it, to the bit.
    /// </summary>
    public static class PhaseCheck
    {
        public static int Run(string directory, bool requireAll)
        {
            Console.WriteLine();
            Console.WriteLine("the docked day, phase by phase (docs/141 slices 3-7)");
            string[] files = Directory.Exists(directory) ? Directory.GetFiles(directory, "*.json.gz") : new string[0];
            Array.Sort(files, string.CompareOrdinal);
            if (files.Length == 0)
            {
                Console.Error.WriteLine("no phase fixtures in " + directory + "; run python -m economy_lab.phase_fixtures");
                return 2;
            }
            int failures = 0;
            SortedDictionary<string, int> unported = new SortedDictionary<string, int>(StringComparer.Ordinal);
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
                    List<JsonElement> states = new List<JsonElement>(root.GetProperty("states").EnumerateArray());
                    List<JsonElement> phases = new List<JsonElement>(root.GetProperty("phases").EnumerateArray());
                    Console.WriteLine("  " + root.GetProperty("case").GetString());
                    for (int k = 0; k < phases.Count; k++)
                    {
                        string name = phases[k].GetString();
                        Action<EconomyState> phase;
                        if (!DockedDay.Ported.TryGetValue(name, out phase))
                        {
                            int seen;
                            unported.TryGetValue(name, out seen);
                            unported[name] = seen + 1;
                            continue;
                        }
                        EconomyState state = StateJson.Read(states[k]);
                        string expected = states[k + 1].GetRawText();
                        string verdict;
                        List<string> differences;
                        try
                        {
                            phase(state);
                            differences = StateCompare.Differences(expected, StateJson.Write(state), 5);
                            verdict = differences.Count == 0 ? "PASS" : "FAIL";
                        }
                        catch (Exception failure)
                        {
                            differences = new List<string> { failure.GetType().Name + ": " + failure.Message };
                            verdict = "FAIL";
                        }
                        bool moved = expected != states[k].GetRawText();
                        Console.WriteLine("    " + verdict + " " + name + (moved ? "" : " (the laboratory's phase changed nothing)"));
                        foreach (string difference in differences)
                        {
                            Console.WriteLine("         " + difference);
                        }
                        if (verdict != "PASS")
                        {
                            failures++;
                        }
                    }
                }
            }
            if (unported.Count > 0)
            {
                Console.WriteLine("  not yet ported: " + string.Join(", ", unported.Keys));
            }
            Console.WriteLine(failures == 0
                ? "every ported phase reproduces the laboratory to the bit"
                : failures + " phase run(s) did NOT reproduce the laboratory");
            if (failures > 0)
            {
                return 5;
            }
            return requireAll && unported.Count > 0 ? 6 : 0;
        }
    }
}
