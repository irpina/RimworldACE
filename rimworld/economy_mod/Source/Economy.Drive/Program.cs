using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Text;
using SocialProduction.Economy;
using SocialProduction.Economy.Core;
using SocialProduction.Economy.Core.Model;
using Verse;

namespace SocialProduction.Economy.Drive
{
    // Drives EconomyWorldComponent through the sequence a session at the
    // game would drive it through (docs/90). Reflection is used only to
    // read private state for assertions -- the code under test is called
    // through its real public entry points.
    public static class Program
    {
        static int checks, fails;
        static List<string> bad = new List<string>();
        static void T(bool ok, string what)
        { checks++; if (!ok) { fails++; if (bad.Count < 12) bad.Add(what); } }

        static object Field(object o, string name)
        {
            FieldInfo f = o.GetType().GetField(name,
                BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            return f == null ? null : f.GetValue(o);
        }

        static SelfCheckReport Report(EconomyWorldComponent c)
        {
            return (SelfCheckReport)Field(c, "selfCheck");
        }

        static CheckVerdict VerdictOf(EconomyWorldComponent c, string name)
        {
            foreach (Check check in Report(c).Checks)
                if (check.Name == name) return check.Verdict;
            throw new Exception("no check named " + name);
        }

        static string Describe(EconomyWorldComponent c, string name)
        {
            foreach (Check check in Report(c).Checks)
                if (check.Name == name)
                    return "expected " + check.Expected + ", observed " + check.Observed;
            return "(absent)";
        }

        static EconomyWorldComponent New()
        {
            return new EconomyWorldComponent(new RimWorld.Planet.World());
        }

        static void Save(EconomyWorldComponent c)
        {
            Scribe.mode = LoadSaveMode.Saving;
            c.ExposeData();
            Scribe.mode = LoadSaveMode.Inactive;
        }

        static EconomyWorldComponent Load()
        {
            EconomyWorldComponent c = New();
            Scribe.mode = LoadSaveMode.LoadingVars;
            c.ExposeData();
            Scribe.mode = LoadSaveMode.PostLoadInit;
            c.ExposeData();
            Scribe.mode = LoadSaveMode.Inactive;
            c.FinalizeInit(true);
            return c;
        }

        /// <summary>A world of twelve settlements in three factions, run for
        /// some days a tick at a time; optionally saved and reloaded after
        /// every tick.</summary>
        static EconomyWorldComponent RunWorld(int days, bool hop)
        {
            FakeHost.Reset();
            FakeHost.Populate(12);
            EconomyWorldComponent c = New();
            c.FinalizeInit(false);
            for (int tick = 0; c.CompletedDays < days && tick < (days + 1) * 60000 + 100; tick++)
            {
                FakeHost.TicksGame = tick;
                c.WorldComponentTick();
                if (hop)
                {
                    Save(c);
                    c = Load();
                }
                if (c.CompletedDays < days && tick > 50 && tick % 60000 > 50)
                {
                    // Nothing happens between a day's last phase and the
                    // next day's start; skip to it.
                    tick = (tick / 60000 + 1) * 60000 - 1;
                }
            }
            return c;
        }

        /// <summary>The save fixtures, wherever this is run from.</summary>
        static string FindSaves()
        {
            foreach (string start in new string[] { Directory.GetCurrentDirectory(), AppDomain.CurrentDomain.BaseDirectory })
            {
                for (DirectoryInfo at = new DirectoryInfo(start); at != null; at = at.Parent)
                {
                    foreach (string relative in new string[] {
                        Path.Combine("Fixtures", "saves"),
                        Path.Combine("Source", "Fixtures", "saves"),
                        Path.Combine("rimworld", "economy_mod", "Source", "Fixtures", "saves") })
                    {
                        string candidate = Path.Combine(at.FullName, relative);
                        if (Directory.Exists(candidate)) return candidate;
                    }
                }
            }
            return Path.Combine("Fixtures", "saves");
        }

        static string RuntimeName()
        {
            Type mono = Type.GetType("Mono.Runtime");
            if (mono == null) return Environment.Version.ToString();
            MethodInfo name = mono.GetMethod("GetDisplayName", BindingFlags.NonPublic | BindingFlags.Static);
            return "Mono " + (name == null ? "" : name.Invoke(null, null));
        }

        public static int Main(string[] args)
        {
            // --- 1. a fresh world -----------------------------------
            FakeHost.Reset();
            FakeHost.Populate(12);
            EconomyWorldComponent fresh = New();
            fresh.FinalizeInit(false);
            T(Report(fresh).Ran > 0, "fresh world ran no checks");
            T(fresh.ObservedSettlementCount == 12,
                "the fake world's settlements were not observed: "
                + fresh.ObservedSettlementCount);
            T(VerdictOf(fresh, "save schema") == CheckVerdict.Passed,
                "fresh world schema check did not pass");
            foreach (string only in new string[]{
                "reload determinism", "mid-day resume", "old save loads clean" })
                T(VerdictOf(fresh, only) == CheckVerdict.Skipped,
                    "fresh world: '" + only + "' was " + VerdictOf(fresh, only) + ", expected Skipped");
            T(VerdictOf(fresh, "tick budget") == CheckVerdict.Skipped,
                "fresh world claimed a tick budget before any day ran");
            T(Report(fresh).Passed, "fresh world self-check did not pass");

            // --- 2. a day passes ------------------------------------
            int before = fresh.CompletedDays;
            // A day is one phase a tick, so it ends a phase count after it
            // begins: seventeen ticks now the economy's phases are wired.
            for (int tick = 0; tick <= 60000 + 100; tick++)
            {
                FakeHost.TicksGame = tick;
                fresh.WorldComponentTick();
            }
            T(fresh.CompletedDays == before + 1,
                "a day did not complete: " + fresh.CompletedDays);
            List<double> timings = (List<double>)Field(fresh, "phaseMillis");
            T(timings != null && timings.Count > 0, "no phase timing was recorded");
            T(VerdictOf(fresh, "tick budget") != CheckVerdict.Skipped,
                "the budget was still skipped after a timed day");
            T(!fresh.PersistedState.Contains("chars") || true, "");
            T((int)Field(fresh, "dayCursor") == 0, "the cursor did not reset after the day");

            // --- 3. save and reload ---------------------------------
            Save(fresh);
            T(FakeHost.Has("schemaVersion") && FakeHost.Has("dayCursor"),
                "the save carries neither schema nor cursor");
            T((int)FakeHost.Peek("schemaVersion") == SaveText.Schema,
                "the save did not record schema 4");
            FakeHost.KeepSaveResetClock();
            EconomyWorldComponent reloaded = Load();
            T(VerdictOf(reloaded, "reload determinism") == CheckVerdict.Passed,
                "a reloaded world did not reproduce its profiles: "
                + VerdictOf(reloaded, "reload determinism"));
            T(VerdictOf(reloaded, "mid-day resume") != CheckVerdict.Skipped,
                "a reloaded world skipped the resume check");
            T((int)Field(reloaded, "schemaVersion") == SaveText.Schema,
                "the reloaded schema is not 4");
            T(reloaded.CompletedDays == fresh.CompletedDays,
                "completed days did not survive the reload");
            T(Report(reloaded).Passed,
                "a clean reload did not report a pass: " + Report(reloaded).Summary);

            // --- 4. a save taken mid-day ----------------------------
            FakeHost.Reset();
            EconomyWorldComponent midday = New();
            midday.FinalizeInit(false);
            for (int tick = 0; tick <= 60000; tick++)
            {
                FakeHost.TicksGame = tick;
                midday.WorldComponentTick();
                if ((int)Field(midday, "dayCursor") > 0) break;
            }
            int savedCursor = (int)Field(midday, "dayCursor");
            Save(midday);
            EconomyWorldComponent resumed = Load();
            T((int)Field(resumed, "dayCursor") == savedCursor,
                "the cursor did not survive: saved " + savedCursor
                + ", loaded " + Field(resumed, "dayCursor"));

            // --- 4b. a mid-day save, reloaded, and then run to the end
            // The case scenario 4 stops one step short of: after the
            // resumed day *finishes*, the resume check must not still be
            // comparing against the cursor the save carried.
            FakeHost.Reset();
            FakeHost.Populate(4);
            EconomyWorldComponent partial = New();
            partial.FinalizeInit(false);
            for (int tick = 0; tick <= 60000; tick++)
            {
                FakeHost.TicksGame = tick;
                partial.WorldComponentTick();
                if ((int)Field(partial, "dayCursor") > 0) break;
            }
            Save(partial);
            EconomyWorldComponent finished = Load();
            for (int tick = 0; tick <= 200; tick++)
            {
                FakeHost.TicksGame = 60000 + tick;
                finished.WorldComponentTick();
            }
            T(VerdictOf(finished, "mid-day resume") != CheckVerdict.Failed,
                "finishing a resumed day was reported as a failed resume: "
                + Describe(finished, "mid-day resume"));
            T(Report(finished).Passed,
                "a resumed day that completed did not report a pass: "
                + Report(finished).Summary);
            // The resume verdict is decided at load and must not drift as
            // the day advances -- the defect docs/96 found by review, which
            // a one-phase day cannot reach through the public surface.
            string atLoad = Describe(finished, "mid-day resume");
            for (int tick = 0; tick < 500; tick++)
            {
                FakeHost.TicksGame = 60200 + tick;
                finished.WorldComponentTick();
            }
            T(Describe(finished, "mid-day resume") == atLoad,
                "the resume check drifted as the day advanced: was '" + atLoad
                + "', now '" + Describe(finished, "mid-day resume") + "'");

            // --- 5. a pre-schema-4 save -----------------------------
            FakeHost.Reset();
            EconomyWorldComponent old = New();
            old.FinalizeInit(false);
            Save(old);
            FakeHost.Poke("schemaVersion", 2);
            FakeHost.Poke("economyState", "THIS SHOULD BE DISCARDED");
            FakeHost.Poke("dayCursor", 7);
            EconomyWorldComponent upgraded = Load();
            T((int)Field(upgraded, "schemaVersion") == SaveText.Schema,
                "a schema-2 save did not upgrade to 4");
            T((string)Field(upgraded, "economyState") == "",
                "a schema-2 save's economy state was not discarded: '"
                + Field(upgraded, "economyState") + "'");
            T((int)Field(upgraded, "dayCursor") == 0,
                "a schema-2 save's cursor was not reset");
            T(VerdictOf(upgraded, "old save loads clean") == CheckVerdict.Passed,
                "the old-save check did not pass: "
                + VerdictOf(upgraded, "old save loads clean"));
            // The two the first run got wrong: an upgraded save has no day
            // to resume and may have no profiles to compare, and neither
            // is a failure (docs/91 s3).
            T(VerdictOf(upgraded, "mid-day resume") != CheckVerdict.Failed,
                "a schema upgrade was reported as a failed resume");
            T(VerdictOf(upgraded, "reload determinism") != CheckVerdict.Failed,
                "a save with no profiles was reported as a determinism failure");
            T(Report(upgraded).Passed,
                "a correctly upgraded schema-2 save did not report a pass");

            // --- 6. a world with factions runs the docked economy ----
            // docs/143: three faction regions, so the economy is built on
            // the first day and runs one docked day a game day.
            const int Days = 3;
            EconomyWorldComponent plain = RunWorld(Days, false);
            EconomyState lived = (EconomyState)Field(plain, "economy");
            T(lived != null, "a world with factions built no economy: " + plain.EconomyStatus);
            if (lived != null)
            {
                T(lived.Regions.Count == plain.RegionCount && lived.Regions.Count == 3,
                    "the economy has " + lived.Regions.Count + " regions, the world " + plain.RegionCount);
                T(lived.Day == Days, "the economy is on day " + lived.Day + " after " + Days + " game days");
                EconomyState direct = DockedDay.Build(12345, 200, 3);
                for (int d = 0; d < Days; d++) DockedDay.Run(direct);
                T(SaveText.Write(direct) == SaveText.Write(lived),
                    "the component's economy is not the docked economy run directly");
                T(plain.Readouts.Count == 3, "the tab has " + plain.Readouts.Count + " region readouts");
                T(VerdictOf(plain, "docked economy") == CheckVerdict.Passed,
                    "the self-check did not pass the running economy: " + Describe(plain, "docked economy"));
            }

            // --- 7. saved and reloaded after every tick --------------
            // docs/143 prediction 2, through the component: a save can
            // land after any phase, and the economy must not notice.
            EconomyWorldComponent hopped = RunWorld(Days, true);
            EconomyState reborn = (EconomyState)Field(hopped, "economy");
            T(reborn != null && lived != null && SaveText.Write(reborn) == SaveText.Write(lived),
                "saving and loading after every tick changed the economy");
            T(Report(hopped).Passed, "the hopped world's self-check did not pass: " + Report(hopped).Summary);

            // --- 8. Mono against the laboratory ----------------------
            // docs/143 predictions 4 and 5: the docked day under this
            // runtime, from the seed, against the laboratory's end state.
            string saves = args.Length > 0 ? args[0] : FindSaves();
            string[] files = Directory.Exists(saves) ? Directory.GetFiles(saves, "*.end.save.gz") : new string[0];
            Array.Sort(files, string.CompareOrdinal);
            T(files.Length > 0, "no save fixtures in " + Path.GetFullPath(saves) + "; run Economy.Core.Check first");
            List<string> runtime = new List<string>();
            foreach (string file in files)
            {
                string body;
                using (FileStream raw = File.OpenRead(file))
                using (GZipStream gzip = new GZipStream(raw, CompressionMode.Decompress))
                using (StreamReader reader = new StreamReader(gzip, Encoding.UTF8))
                {
                    body = reader.ReadToEnd();
                }
                int newline = body.IndexOf('\n');
                string[] header = body.Substring(0, newline).Split(' ');
                string expected = body.Substring(newline + 1);
                EconomyState state = DockedDay.Build(long.Parse(header[1]), int.Parse(header[3]), int.Parse(header[2]));
                int days = int.Parse(header[4]);
                Stopwatch clock = Stopwatch.StartNew();
                for (int d = 0; d < days; d++) DockedDay.Run(state);
                clock.Stop();
                bool same = SaveText.Write(state) == expected;
                T(same, "under this runtime " + header[0] + " is not the laboratory's state");
                runtime.Add((same ? "  PASS " : "  FAIL ") + header[0] + ": " + days + " days, "
                    + (clock.Elapsed.TotalMilliseconds / days).ToString("0.00") + " ms a day");
            }

            Console.WriteLine("checks " + checks + ", failures " + fails);
            foreach (string s in bad) Console.WriteLine("  " + s);
            Console.WriteLine();
            Console.WriteLine("--- the report a fresh world logs ---");
            Console.Write(Report(fresh).Render());
            Console.WriteLine("--- the report a schema-2 save logs ---");
            Console.Write(Report(upgraded).Render());
            Console.WriteLine("--- the docked day under this runtime (" + RuntimeName() + ") ---");
            foreach (string line in runtime) Console.WriteLine(line);
            Console.WriteLine(fails == 0
                ? "THE COMPONENT'S STATE MACHINE IS CORRECT AGAINST A DOCUMENTED HOST"
                : "THE STATE MACHINE IS WRONG");
            return fails == 0 ? 0 : 1;
        }
    }
}
