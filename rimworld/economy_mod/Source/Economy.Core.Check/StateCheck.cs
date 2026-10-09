using System;
using System.Collections.Generic;
using System.IO;
using SocialProduction.Economy.Core.Model;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// docs/141 slice 1: every state fixture the laboratory wrote is read
    /// into the port's state model and written back, and the two must agree
    /// field for field, in order, to the bit.
    /// </summary>
    public static class StateCheck
    {
        /// <summary>
        /// A comparison that cannot fail proves nothing. One producer's cash
        /// moved by a single ulp, and two inventory entries swapped, must
        /// each be reported, and nothing else.
        /// </summary>
        private static int NegativeControls(string file)
        {
            string expected = File.ReadAllText(file);
            int failures = 0;

            EconomyState state = StateJson.Read(expected);
            Producer producer = state.Regions.ValueAt(0).Producers[0];
            producer.Cash = BitConverter.Int64BitsToDouble(BitConverter.DoubleToInt64Bits(producer.Cash) + 1);
            List<string> ulp = StateCompare.Differences(expected, StateJson.Write(state), 5);
            bool caught = ulp.Count == 1 && ulp[0].Contains(".cash") && ulp[0].Contains("(1 ulp)");
            Console.WriteLine("  " + (caught ? "PASS" : "FAIL") + " negative control, one ulp of one producer's cash: "
                + (ulp.Count == 0 ? "not seen" : ulp[0]));
            failures += caught ? 0 : 1;

            state = StateJson.Read(expected);
            OrderedMap<double> inventory = state.Regions.ValueAt(0).Inventory;
            string first = inventory.KeyAt(0);
            double amount = inventory.Remove(first);
            inventory[first] = amount;
            List<string> order = StateCompare.Differences(expected, StateJson.Write(state), 5);
            caught = order.Count == 1 && order[0].Contains("inventory: entry 0");
            Console.WriteLine("  " + (caught ? "PASS" : "FAIL") + " negative control, one inventory entry moved to the end: "
                + (order.Count == 0 ? "not seen" : order[0]));
            failures += caught ? 0 : 1;
            return failures;
        }

        public static int Run(string directory)
        {
            Console.WriteLine();
            Console.WriteLine("state round trip (docs/141 slice 1)");
            if (!Directory.Exists(directory))
            {
                Console.Error.WriteLine("no state fixtures at " + directory + "; run python -m economy_lab.state_fixtures");
                return 2;
            }
            string[] files = Directory.GetFiles(directory, "*.json");
            Array.Sort(files, string.CompareOrdinal);
            int failures = 0;
            foreach (string file in files)
            {
                string expected = File.ReadAllText(file);
                EconomyState state = StateJson.Read(expected);
                string observed = StateJson.Write(state);
                List<string> differences = StateCompare.Differences(expected, observed, 5);
                int producers = 0;
                for (int i = 0; i < state.Regions.Count; i++)
                {
                    producers += state.Regions.ValueAt(i).Producers.Count;
                }
                Console.WriteLine("  " + (differences.Count == 0 ? "PASS " : "FAIL ") + Path.GetFileName(file)
                    + ": day " + state.Day + ", " + state.Regions.Count + " regions, "
                    + state.Commodities.Count + " commodities, " + producers + " producers");
                foreach (string difference in differences)
                {
                    Console.WriteLine("       " + difference);
                }
                if (differences.Count > 0)
                {
                    failures++;
                }
            }
            if (files.Length == 0)
            {
                Console.Error.WriteLine("no state fixtures in " + directory);
                return 2;
            }
            failures += NegativeControls(files[0]);
            Console.WriteLine(failures == 0
                ? "every state fixture round-trips to the bit"
                : failures + " state fixture(s) did NOT round-trip");
            return failures == 0 ? 0 : 4;
        }
    }
}
