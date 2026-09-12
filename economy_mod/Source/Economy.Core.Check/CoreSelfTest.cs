using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using SocialProduction.Economy.Core;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// The properties of the parts that have no fixtures: the codec
    /// (docs/81), the scheduler (docs/83), the wealth coupling
    /// (docs/85), and the self-check and tick budget (docs/89).
    ///
    /// These were measured once in a session's scratchpad and are
    /// committed here because verification that cannot be re-run is not
    /// verification (docs/92).
    /// </summary>
    public static class CoreSelfTest
    {
        private static int checks;
        private static int failures;
        private static readonly List<string> firstFew = new List<string>();

        private static void T(bool ok, string what)
        {
            checks++;
            if (!ok)
            {
                failures++;
                if (firstFew.Count < 12) firstFew.Add(what);
            }
        }

        public static int Run(string fixturesRoot)
        {
            checks = 0;
            failures = 0;
            firstFew.Clear();

            CodecRoundTrip(fixturesRoot);
            Readout();
            SchedulerInvariant();
            WealthProperties();
            ReportAndBudget();

            Console.WriteLine();
            Console.WriteLine("core self-test: " + checks + " checks, " + failures + " failures");
            foreach (string line in firstFew) Console.WriteLine("  " + line);
            Console.WriteLine(failures == 0
                ? "codec, scheduler, wealth coupling and self-check all hold"
                : "A CORE PROPERTY IS BROKEN");
            return failures == 0 ? 0 : 1;
        }

        /// <summary>Every double in every fixture survives the codec (docs/81).</summary>
        private static void CodecRoundTrip(string fixturesRoot)
        {
            List<double> values = new List<double>();
            if (Directory.Exists(fixturesRoot))
            {
                foreach (string dir in Directory.GetDirectories(fixturesRoot))
                {
                    foreach (string file in Directory.GetFiles(dir, "*.json"))
                    {
                        using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(file)))
                        {
                            Walk(document.RootElement, values);
                        }
                    }
                }
            }
            T(values.Count > 0, "no fixture doubles found to round-trip");
            HashSet<long> seen = new HashSet<long>();
            EconomySnapshot snapshot = new EconomySnapshot();
            RegionSnapshot region = new RegionSnapshot();
            region.Name = "Dust Basin";
            int i = 0;
            int bad = 0;
            foreach (double value in values)
            {
                if (!seen.Add(BitConverter.DoubleToInt64Bits(value))) continue;
                if (StateCodec.Decode(StateCodec.Encode(value)) != value) bad++;
                string key = "g" + i;
                if (i % 2 == 0) snapshot.LaborValues.Add(new Quantity(key, value));
                else region.Prices.Add(new Quantity(key, value));
                i++;
            }
            snapshot.Regions.Add(region);
            T(bad == 0, bad + " doubles did not survive Encode/Decode");
            EconomySnapshot back = StateCodec.Read(StateCodec.Write(snapshot));
            T(back.Regions.Count == 1 && back.Regions[0].Name == region.Name,
                "the snapshot's region did not survive Write/Read");
            T(Same(snapshot.LaborValues, back.LaborValues), "labor values did not survive the snapshot");
            T(Same(region.Prices, back.Regions[0].Prices), "prices did not survive the snapshot");
        }

        private static bool Same(List<Quantity> a, List<Quantity> b)
        {
            if (a.Count != b.Count) return false;
            for (int i = 0; i < a.Count; i++)
            {
                if (a[i].Name != b[i].Name) return false;
                if (BitConverter.DoubleToInt64Bits(a[i].Amount)
                    != BitConverter.DoubleToInt64Bits(b[i].Amount)) return false;
            }
            return true;
        }

        private static void Walk(JsonElement node, List<double> into)
        {
            switch (node.ValueKind)
            {
                case JsonValueKind.Object:
                    foreach (JsonProperty p in node.EnumerateObject()) Walk(p.Value, into);
                    break;
                case JsonValueKind.Array:
                    foreach (JsonElement e in node.EnumerateArray()) Walk(e, into);
                    break;
                case JsonValueKind.Number:
                    into.Add(node.GetDouble());
                    break;
            }
        }

        /// <summary>The readout is right, and survivable (docs/94).</summary>
        private static void Readout()
        {
            Dictionary<string, double> values = new Dictionary<string, double>();
            Dictionary<string, double> prices = new Dictionary<string, double>();
            Dictionary<string, double> rent = new Dictionary<string, double>();
            Dictionary<string, double> output = new Dictionary<string, double>();
            double ticksPerDay = 24000.0;
            double wage = 41.97;

            // A commodity priced exactly at its value at this region's wage.
            values["atvalue"] = 0.5 * ticksPerDay;      // half a worker-day
            prices["atvalue"] = 0.5 * wage;             // ... in silver
            // One at twice its value, which is the deviation the mod is about.
            values["dear"] = 0.25 * ticksPerDay;
            prices["dear"] = 0.5 * wage;
            // And the degenerate cases, which must not reach a player as NaN.
            values["novalue"] = 0.0;
            prices["novalue"] = 12.0;
            prices["nopricevalue"] = 0.0;
            values["nan"] = double.NaN;
            prices["nan"] = double.PositiveInfinity;
            rent["dear"] = 30.0;
            output["dear"] = 10.0;
            rent["nan"] = double.NaN;
            output["nan"] = 0.0;

            RegionReadout readout = EconomyReadout.Build(
                "Dust Basin", values, prices, rent, output,
                ticksPerDay, wage, 275.0, 412.5, 0.3175);

            Dictionary<string, ReadoutRow> rows = new Dictionary<string, ReadoutRow>();
            foreach (ReadoutRow row in readout.Rows) rows[row.Commodity] = row;

            T(rows.Count == readout.Rows.Count, "the readout produced duplicate rows");
            T(rows["atvalue"].ValueWorkerDays == 0.5,
                "worker-days is not the value over the working day");
            // 3.2: exactly 1.0 at equality, and a pure number.
            T(rows["atvalue"].PriceOverValue == 1.0,
                "price over value is not exactly 1.0 at equality: "
                + rows["atvalue"].PriceOverValue);
            T(Math.Abs(rows["dear"].PriceOverValue - 2.0) < 1e-12,
                "a commodity at twice its value did not read 2.0");
            // The ratio must not depend on how long a tick is.
            RegionReadout doubled = EconomyReadout.Build(
                "Dust Basin", Scale(values, 2.0), prices, rent, output,
                ticksPerDay * 2.0, wage, 275.0, 412.5, 0.3175);
            foreach (ReadoutRow row in doubled.Rows)
                if (row.Commodity == "atvalue")
                    T(row.PriceOverValue == 1.0,
                        "the ratio moved when the tick length did");

            // 3.3
            T(Math.Abs(readout.RateOfSurplusValue - 1.5) < 1e-12,
                "the rate of surplus value is not surplus over necessary");
            RegionReadout noBasket = EconomyReadout.Build(
                "Nowhere", values, prices, rent, output, ticksPerDay, wage, 0.0, 5.0, 0.0);
            T(noBasket.RateOfSurplusValue < 0.0, "a region with no basket got a rate anyway");
            T(EconomyReadout.Ratio(noBasket.RateOfSurplusValue) == "n/a",
                "an uncomputable rate did not render as n/a");

            // 3.4: nothing reaches a player as NaN or infinity.
            foreach (ReadoutRow row in readout.Rows)
            {
                T(!double.IsNaN(row.ValueWorkerDays) && !double.IsInfinity(row.ValueWorkerDays),
                    row.Commodity + ": value is not a number");
                T(!double.IsNaN(row.Price) && !double.IsInfinity(row.Price),
                    row.Commodity + ": price is not a number");
                T(!double.IsNaN(row.RentShare) && !double.IsInfinity(row.RentShare),
                    row.Commodity + ": rent share is not a number");
                string rendered = EconomyReadout.Number(row.ValueWorkerDays)
                    + EconomyReadout.Ratio(row.PriceOverValue)
                    + EconomyReadout.Percent(row.RentShare);
                T(rendered.IndexOf("NaN", StringComparison.Ordinal) < 0
                    && rendered.IndexOf("Inf", StringComparison.Ordinal) < 0
                    && rendered.IndexOf("\u221E", StringComparison.Ordinal) < 0,
                    row.Commodity + ": rendered as '" + rendered + "'");
            }
            T(rows["novalue"].PriceOverValue < 0.0,
                "a commodity with no value reported a ratio anyway");
            T(EconomyReadout.Number(double.NaN) == "n/a", "NaN did not render as n/a");
            T(EconomyReadout.Number(double.PositiveInfinity) == "n/a",
                "infinity did not render as n/a");
            // 30 silver of rent on 10 units at 20.985 silver = 14.29%
            T(Math.Abs(rows["dear"].RentShare - 30.0 / (10.0 * prices["dear"])) < 1e-12,
                "the rent share is not rent over the sector's value");
            T(EconomyReadout.Headline(readout).Contains("s/v 1.5x"),
                "the headline does not carry the rate: "
                + EconomyReadout.Headline(readout));
        }

        private static Dictionary<string, double> Scale(
            Dictionary<string, double> source, double factor)
        {
            Dictionary<string, double> scaled = new Dictionary<string, double>();
            foreach (KeyValuePair<string, double> entry in source)
                scaled[entry.Key] = entry.Value * factor;
            return scaled;
        }

        /// <summary>Spreading a day across ticks does not change it (docs/83).</summary>
        private static void SchedulerInvariant()
        {
            string order = null;
            string reference = null;
            for (int budget = 0; budget <= 8; budget++)
            {
                List<string> log = new List<string>();
                double accumulator = 0.0;
                List<IDayPhase> phases = new List<IDayPhase>();
                for (int i = 0; i < 4; i++)
                {
                    int n = i;
                    phases.Add(new DayPhase("p" + n, delegate
                    {
                        accumulator = accumulator * 1.7 + (n + 1) * 0.31;
                        log.Add("p" + n);
                    }));
                }
                DayScheduler scheduler = new DayScheduler(phases);
                scheduler.BeginDay();
                if (budget == 0)
                {
                    scheduler.RunWholeDay();
                }
                else
                {
                    int guard = 0;
                    while (!scheduler.DayComplete && guard++ < 100) scheduler.AdvanceTick(budget);
                }
                string state = BitConverter.DoubleToInt64Bits(accumulator).ToString("x16");
                string sequence = string.Join(",", log.ToArray());
                if (reference == null) { reference = state; order = sequence; }
                T(state == reference, "budget " + budget + " changed the day's result");
                T(sequence == order, "budget " + budget + " changed the phase order");
                T(scheduler.DayComplete, "budget " + budget + " left the day unfinished");
            }
        }

        /// <summary>The default is inert and the bound holds (docs/85).</summary>
        private static void WealthProperties()
        {
            double[] prices = { 0.0, 0.01, 1.0, 3.0, 1e6, double.NaN,
                                double.PositiveInfinity, -5.0 };
            double[] authored = { 0.0, 0.01, 2.3, 100.0, double.NaN, -1.0 };
            double[] bands = { 0.0, 0.25, 1.0, double.NaN, -0.5 };
            foreach (double p in prices)
                foreach (double a in authored)
                    foreach (double b in bands)
                    {
                        T(WealthCoupling.Factor(WealthMode.Observe, p, a, b) == 1.0,
                            "Observe was not exactly 1.0");
                        double f = WealthCoupling.Factor(WealthMode.Bounded, p, a, b);
                        double safe = (!double.IsNaN(b) && !double.IsInfinity(b) && b > 0.0) ? b : 0.0;
                        double high = 1.0 + safe;
                        T(!double.IsNaN(f) && !double.IsInfinity(f) && f >= 1.0 / high && f <= high,
                            "Bounded escaped its band");
                    }
            List<Quantity> stocks = new List<Quantity>();
            Dictionary<string, double> tripled = new Dictionary<string, double>();
            Dictionary<string, double> vanilla = new Dictionary<string, double>();
            for (int i = 0; i < 5; i++)
            {
                string g = "g" + i;
                stocks.Add(new Quantity(g, 10.0 * (i + 1)));
                vanilla[g] = 2.3 * (i + 1);
                tripled[g] = vanilla[g] * 3.0;
            }
            T(WealthCoupling.ProjectedWealthRatio(WealthMode.Observe, stocks, tripled, vanilla, 0.25) == 1.0,
                "a tripling moved the default mode");
            T(Math.Abs(WealthCoupling.ProjectedWealthRatio(
                WealthMode.Unbounded, stocks, tripled, vanilla, 0.25) - 3.0) < 1e-12,
                "Unbounded did not show the tripling");
            double bounded = WealthCoupling.ProjectedWealthRatio(
                WealthMode.Bounded, stocks, tripled, vanilla, 0.25);
            T(bounded >= 1.0 / 1.25 && bounded <= 1.25, "the bounded portfolio escaped its band");
        }

        /// <summary>An empty report is not a pass; the budget is sane (docs/89).</summary>
        private static void ReportAndBudget()
        {
            T(!new SelfCheckReport().Passed, "an empty report passed");
            SelfCheckReport skipped = new SelfCheckReport();
            skipped.Add("x", "1", "1", CheckVerdict.Skipped);
            T(!skipped.Passed, "an all-skipped report passed");
            SelfCheckReport good = new SelfCheckReport();
            good.Expect("a", "1", "1");
            T(good.Passed, "a passing report did not pass");
            SelfCheckReport bad = new SelfCheckReport();
            bad.Expect("a", "1", "2");
            T(!bad.Passed && bad.Render().Contains("FAIL a"), "a failing report did not fail");

            double[][] sets = {
                new double[]{0.05,0.05,0.05,0.05}, new double[]{9.0,9.0},
                new double[]{double.NaN,0.1}, new double[]{-1.0,0.1}, new double[]{1e9},
            };
            double[] budgets = { 2.0, 0.0, -1.0, double.NaN, 1e9 };
            foreach (double[] set in sets)
                foreach (double b in budgets)
                {
                    List<double> timings = new List<double>(set);
                    int rec = TickBudget.Recommend(timings, b);
                    T(rec >= 1 && rec <= timings.Count, "the recommendation left its range");
                }
            T(TickBudget.Recommend(new List<double>(new double[]{0.05,0.05,0.05,0.05}), 2.0) == 4,
                "comfortable timings did not run the whole day");
            T(TickBudget.BudgetUnreachable(new List<double>(new double[]{9.0,9.0}), 2.0),
                "an oversized phase was not reported unreachable");
        }
    }
}
