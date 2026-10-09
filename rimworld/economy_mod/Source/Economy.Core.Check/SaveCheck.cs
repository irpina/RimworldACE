using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using SocialProduction.Economy.Core.Model;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// docs/143 predictions 1 to 3: the game's save format carries every
    /// state the fixtures hold, a run saved and reloaded after every phase
    /// is the run that never was, and how large a save is.
    /// </summary>
    public static class SaveCheck
    {
        public static int Run(string fixtures)
        {
            Console.WriteLine();
            Console.WriteLine("the save format (docs/143)");
            int failures = 0;

            // Prediction 1: every state the fixtures hold round-trips.
            List<KeyValuePair<string, string>> states = new List<KeyValuePair<string, string>>();
            foreach (string file in Sorted(Path.Combine(fixtures, "state"), "*.json"))
            {
                states.Add(new KeyValuePair<string, string>(Path.GetFileName(file), File.ReadAllText(file)));
            }
            foreach (string file in Sorted(Path.Combine(fixtures, "phases"), "*.json.gz"))
            {
                using (JsonDocument document = JsonDocument.Parse(Gunzip(file)))
                {
                    int index = 0;
                    foreach (JsonElement state in document.RootElement.GetProperty("states").EnumerateArray())
                    {
                        states.Add(new KeyValuePair<string, string>(Path.GetFileName(file) + "#" + index++, state.GetRawText()));
                    }
                }
            }
            foreach (string file in Sorted(Path.Combine(fixtures, "runs"), "*.json.gz"))
            {
                using (JsonDocument document = JsonDocument.Parse(Gunzip(file)))
                {
                    states.Add(new KeyValuePair<string, string>(Path.GetFileName(file) + "#start", document.RootElement.GetProperty("start").GetRawText()));
                    states.Add(new KeyValuePair<string, string>(Path.GetFileName(file) + "#end", document.RootElement.GetProperty("end").GetRawText()));
                }
            }
            int bad = 0;
            foreach (KeyValuePair<string, string> state in states)
            {
                string why = RoundTrip(state.Value);
                if (why != null)
                {
                    bad++;
                    if (bad <= 5)
                    {
                        Console.WriteLine("       " + state.Key + ": " + why);
                    }
                }
            }
            Console.WriteLine("  " + (bad == 0 ? "PASS " : "FAIL ") + states.Count + " fixture states round-trip through the save format"
                + (bad == 0 ? "" : " (" + bad + " did not)"));
            failures += bad == 0 ? 0 : 1;

            // A corrupted save must be refused, not misread.
            EconomyState small = StateJson.Read(states[0].Value);
            string good = SaveText.Write(small);
            string[] corruptions = { good.Substring(0, good.Length / 2), good + " 0", good.Replace(" s", " x") };
            int refused = 0;
            foreach (string corrupt in corruptions)
            {
                try { SaveText.Read(corrupt); }
                catch (InvalidDataException) { refused++; }
            }
            Console.WriteLine("  " + (refused == corruptions.Length ? "PASS " : "FAIL ") + "control: "
                + refused + " of " + corruptions.Length + " corrupted saves refused");
            failures += refused == corruptions.Length ? 0 : 1;

            // Predictions 2 and 3: save and load between every phase.
            foreach (string file in Sorted(Path.Combine(fixtures, "runs"), "*.json.gz"))
            {
                using (JsonDocument document = JsonDocument.Parse(Gunzip(file)))
                {
                    JsonElement root = document.RootElement;
                    string name = root.GetProperty("case").GetString();
                    int days = root.GetProperty("days").GetInt32();
                    EconomyState state = StateJson.Read(root.GetProperty("start"));
                    string text = SaveText.Write(state);
                    int bytes = Encoding.UTF8.GetByteCount(text);
                    Stopwatch codec = new Stopwatch();
                    int saves = 0;
                    List<string> differences;
                    try
                    {
                        for (int d = 0; d < days; d++)
                        {
                            foreach (DockedDay.Phase phase in DockedDay.Order)
                            {
                                phase.Run(state);
                                codec.Start();
                                state = SaveText.Read(SaveText.Write(state));
                                codec.Stop();
                                saves++;
                            }
                        }
                        differences = StateCompare.Differences(root.GetProperty("end").GetRawText(), StateJson.Write(state), 5);
                    }
                    catch (Exception failure)
                    {
                        differences = new List<string> { failure.GetType().Name + " on day " + state.Day + ": " + failure.Message };
                    }
                    Console.WriteLine("  " + (differences.Count == 0 ? "PASS " : "FAIL ") + name + ": saved and loaded after each of "
                        + saves + " phases; start state " + (bytes / 1024.0 / 1024.0).ToString("0.00") + " MB, "
                        + (codec.Elapsed.TotalMilliseconds / Math.Max(saves, 1)).ToString("0.0") + " ms a save and load");
                    foreach (string difference in differences)
                    {
                        Console.WriteLine("       " + difference);
                    }
                    failures += differences.Count == 0 ? 0 : 1;
                }
            }
            Console.WriteLine(failures == 0 ? "the save format carries the state to the bit" : failures + " save check(s) failed");
            return failures == 0 ? 0 : 1;
        }

        private static string RoundTrip(string json)
        {
            EconomyState original = StateJson.Read(json);
            string text = SaveText.Write(original);
            EconomyState decoded = SaveText.Read(text);
            if (SaveText.Write(decoded) != text)
            {
                return "re-encoding the decoded state changed the text";
            }
            List<string> differences = StateCompare.Differences(StateJson.Write(original), StateJson.Write(decoded), 1);
            return differences.Count == 0 ? null : differences[0];
        }

        private static string[] Sorted(string directory, string pattern)
        {
            string[] files = Directory.Exists(directory) ? Directory.GetFiles(directory, pattern) : new string[0];
            Array.Sort(files, string.CompareOrdinal);
            return files;
        }

        private static string Gunzip(string file)
        {
            using (FileStream raw = File.OpenRead(file))
            using (GZipStream gzip = new GZipStream(raw, CompressionMode.Decompress))
            using (StreamReader reader = new StreamReader(gzip))
            {
                return reader.ReadToEnd();
            }
        }
    }
}
