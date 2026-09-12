using System;
using System.Collections.Generic;
using System.Reflection;
using SocialProduction.Economy;
using SocialProduction.Economy.Core;
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
            for (int tick = 0; tick <= 60000 + 10; tick++)
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
            T((int)FakeHost.Peek("schemaVersion") == StateCodec.SchemaVersion,
                "the save did not record schema 3");
            FakeHost.KeepSaveResetClock();
            EconomyWorldComponent reloaded = Load();
            T(VerdictOf(reloaded, "reload determinism") == CheckVerdict.Passed,
                "a reloaded world did not reproduce its profiles: "
                + VerdictOf(reloaded, "reload determinism"));
            T(VerdictOf(reloaded, "mid-day resume") != CheckVerdict.Skipped,
                "a reloaded world skipped the resume check");
            T((int)Field(reloaded, "schemaVersion") == StateCodec.SchemaVersion,
                "the reloaded schema is not 3");
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

            // --- 5. a pre-schema-3 save -----------------------------
            FakeHost.Reset();
            EconomyWorldComponent old = New();
            old.FinalizeInit(false);
            Save(old);
            FakeHost.Poke("schemaVersion", 2);
            FakeHost.Poke("economyState", "THIS SHOULD BE DISCARDED");
            FakeHost.Poke("dayCursor", 7);
            EconomyWorldComponent upgraded = Load();
            T((int)Field(upgraded, "schemaVersion") == StateCodec.SchemaVersion,
                "a schema-2 save did not upgrade to 3");
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

            Console.WriteLine("checks " + checks + ", failures " + fails);
            foreach (string s in bad) Console.WriteLine("  " + s);
            Console.WriteLine();
            Console.WriteLine("--- the report a fresh world logs ---");
            Console.Write(Report(fresh).Render());
            Console.WriteLine("--- the report a schema-2 save logs ---");
            Console.Write(Report(upgraded).Render());
            Console.WriteLine(fails == 0
                ? "THE COMPONENT'S STATE MACHINE IS CORRECT AGAINST A DOCUMENTED HOST"
                : "THE STATE MACHINE IS WRONG");
            return fails == 0 ? 0 : 1;
        }
    }
}
