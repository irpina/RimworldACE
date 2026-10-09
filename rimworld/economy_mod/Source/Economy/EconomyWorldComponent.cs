using System.Collections.Generic;
using System.Diagnostics;
using RimWorld.Planet;
using SocialProduction.Economy.Core;
using SocialProduction.Economy.Core.Model;
using Verse;

namespace SocialProduction.Economy
{
    public sealed class EconomyWorldComponent : WorldComponent
    {
        private const int TicksPerDay = 60000;

        /// <summary>
        /// Schema 2 is the profiles-only shell and schema 3 the snapshot of
        /// docs/80. Schema 4 carries the whole docked economy (docs/143):
        /// an older save loads with no economy and builds one, rather than
        /// read its fields as something they are not.
        /// </summary>
        private const int SaveSchemaVersion = SaveText.Schema;

        /// <summary>
        /// The docked economy's size: the battery's 200 commodities, the
        /// size that docked. The laboratory refuses the full population
        /// until its fund scales with the economy (docs/142, docs/143 s2).
        /// </summary>
        private const int Commodities = 200;

        /// <summary>
        /// Phases run per tick. A count, not a duration, because the
        /// scheduler must not consult the clock (docs/82 section 3) — the
        /// clock lives here, on the side that cannot be tested outside the
        /// game, and hands the deterministic side a number.
        ///
        /// One is the conservative starting value: it spreads a four-phase
        /// day over four ticks, which is 4/60 of a second at 1×, against a
        /// day that is 60,000 ticks long. **It is a guess, and the first
        /// thing to profile in game** (docs/83 section 5).
        /// </summary>
        private const int PhasesPerTick = 1;

        private int schemaVersion = SaveSchemaVersion;
        private int completedDays;
        private int lastProcessedTick = -1;
        private int observedSettlementCount;
        private List<SettlementProfile> profiles = new List<SettlementProfile>();
        private int regionCount;
        private string determinismStatus = "not checked";

        /// <summary>
        /// The economy, encoded (docs/81). One `Scribe_Values.Look` on one
        /// string rather than one per field: the codec is the only thing
        /// that knows how a number is spelled, so nobody can add a field
        /// and accidentally write a bare double through Mono's decimal
        /// formatter.
        /// </summary>
        private string economyState = "";

        /// <summary>
        /// Which phase of the day runs next, persisted because a save can
        /// land mid-day and re-running a phase is not harmless: the wage
        /// settlement pays a wage bill (docs/83 section 3).
        /// </summary>
        private int dayCursor;

        private DayScheduler scheduler;

        /// <summary>
        /// The docked economy (docs/141), live. Persisted through
        /// <see cref="economyState"/> in the save format of docs/143, and
        /// built on the first day the world has a faction region.
        /// </summary>
        private EconomyState economy;

        /// <summary>Why the economy is not running, when it should be.</summary>
        private string economyFailure;

        /// <summary>
        /// What the mod found when it checked itself, on load (docs/88).
        /// The game produces the evidence rather than the person: a
        /// report can be pasted, re-checked and contradicted by a later
        /// run, and an impression cannot.
        /// </summary>
        private SelfCheckReport selfCheck = new SelfCheckReport();

        /// <summary>Milliseconds each phase of the last day took, for the budget.</summary>
        private readonly List<double> phaseMillis = new List<double>();

        private int schemaOnLoad = -1;
        private int cursorOnLoad;

        /// <summary>
        /// Whether this world came from a save. Remembered because the
        /// self-check is re-run after the first day, and re-running it as
        /// if loaded would fail the load-only checks on a fresh world —
        /// a check must not report a failure for a case that does not
        /// apply (docs/88 section 5.2's distinction, one level up).
        /// </summary>
        private bool loadedFromSave;

        /// <summary>
        /// The resume check's verdict, decided **once, at load**, because
        /// that is the only moment it is about.
        ///
        /// The first version recomputed it from the live scheduler every
        /// time the report was rebuilt, so once a resumed day finished it
        /// compared the cursor the save carried against the cursor the
        /// finished day left — and reported a correct resume as a failure.
        /// Latent while a day has one phase and certain the moment it has
        /// two, which is why it was found by review rather than by the
        /// harness (docs/96).
        /// </summary>
        private Check resumeCheck;

        public EconomyWorldComponent(World world) : base(world)
        {
        }

        public int CompletedDays => completedDays;

        public int ObservedSettlementCount => observedSettlementCount;

        public int RegionCount => regionCount;

        public IReadOnlyList<SettlementProfile> Profiles => profiles;

        /// <summary>
        /// What the reload comparison found, for display in the tab.
        ///
        /// The profiles are a pure function of the saved world, so a reload
        /// must re-derive exactly what was stored. This says whether it did.
        /// </summary>
        public string DeterminismStatus => determinismStatus;

        /// <summary>How far through the current day the scheduler is, for the tab.</summary>
        public string DayProgress =>
            scheduler == null || scheduler.DayComplete
                ? "idle"
                : "phase " + (scheduler.Cursor + 1) + " of " + scheduler.PhaseCount;

        /// <summary>
        /// The economy in units a player has: worker-days, price over
        /// value, the rate of surplus value, rent as a share (docs/94).
        ///
        /// Empty until the model is wired to the world and the snapshot
        /// carries an economy — the readout is built and checked, and
        /// what it has to read is the last thing the port needs.
        /// </summary>
        public IReadOnlyList<RegionReadout> Readouts => readouts;

        private List<RegionReadout> readouts = new List<RegionReadout>();

        /// <summary>Whether this save carries economy state, and how much.</summary>
        /// <summary>The self-check, rendered; what a session at the game pastes back.</summary>
        public string SelfCheckText => selfCheck.Render();

        public string SelfCheckSummary => selfCheck.Summary;

        public string PersistedState =>
            string.IsNullOrEmpty(economyState)
                ? "none yet (schema " + schemaVersion + ")"
                : economyState.Length + " chars, bit-exact encoding";

        /// <summary>The docked economy in one line, for the tab.</summary>
        public string EconomyStatus
        {
            get
            {
                if (economyFailure != null)
                {
                    return "stopped: " + economyFailure;
                }
                if (economy == null)
                {
                    return regionCount == 0
                        ? "waiting for a faction region"
                        : "built at the start of the next day";
                }
                int producers = 0;
                int active = 0;
                for (int r = 0; r < economy.Regions.Count; r++)
                {
                    foreach (Producer producer in economy.Regions.ValueAt(r).Producers)
                    {
                        producers++;
                        if (producer.Active && producer.LastRuns > 0.0)
                        {
                            active++;
                        }
                    }
                }
                return "day " + economy.Day + ", " + economy.Regions.Count + " regions, "
                    + economy.Commodities.Count + " commodities, "
                    + active + " of " + producers + " producers working";
            }
        }

        public override void FinalizeInit(bool fromLoad)
        {
            base.FinalizeInit(fromLoad);

            List<SettlementProfile> derived = ProfileBuilder.Build();
            if (fromLoad && profiles != null && profiles.Count > 0)
            {
                determinismStatus = CompareWithLoaded(derived);
            }
            else
            {
                determinismStatus = fromLoad
                    ? "nothing saved to compare"
                    : "fresh world";
            }
            Adopt(derived);

            if (lastProcessedTick < 0 && Find.TickManager != null)
            {
                lastProcessedTick = Find.TickManager.TicksGame;
            }

            loadedFromSave = fromLoad;
            RunSelfCheck(fromLoad);

            Log.Message(
                "[Social Production: Economy] Stage 1 read-only component ready: "
                + observedSettlementCount + " settlements in " + regionCount
                + " regions; determinism check: " + determinismStatus
                + ". Vanilla trade prices are unchanged.");
            Log.Message(selfCheck.Render());
        }

        /// <summary>
        /// Re-derive on load and say whether it reproduced what was saved.
        ///
        /// This is the whole reason the profiles are persisted at all. They
        /// are a pure function of the world, so storing them is redundant
        /// *unless* the stored copy is used to check the function stayed
        /// pure. A mismatch means something in the derivation depends on
        /// state that is not in the save, which would be invisible otherwise
        /// and fatal later.
        ///
        /// Reported rather than thrown: a settlement destroyed between save
        /// and load is a legitimate difference, and a component that refused
        /// to load a valid save would be far worse than one that says what it
        /// found.
        /// </summary>
        private string CompareWithLoaded(List<SettlementProfile> derived)
        {
            Dictionary<int, SettlementProfile> saved =
                new Dictionary<int, SettlementProfile>();
            foreach (SettlementProfile profile in profiles)
            {
                if (profile != null)
                {
                    saved[profile.SettlementId] = profile;
                }
            }

            int matched = 0;
            int changed = 0;
            int added = 0;
            SettlementProfile firstChange = null;
            foreach (SettlementProfile profile in derived)
            {
                SettlementProfile before;
                if (!saved.TryGetValue(profile.SettlementId, out before))
                {
                    added++;
                    continue;
                }
                saved.Remove(profile.SettlementId);
                if (profile.Matches(before))
                {
                    matched++;
                }
                else
                {
                    changed++;
                    if (firstChange == null)
                    {
                        firstChange = profile;
                        Log.Warning(
                            "[Social Production: Economy] Reload re-derived a "
                            + "different profile. Saved: " + before.Describe()
                            + " -- derived: " + profile.Describe());
                    }
                }
            }

            int removed = saved.Count;
            if (changed == 0 && added == 0 && removed == 0)
            {
                return "reproduced " + matched + "/" + matched + " on reload";
            }
            return "reproduced " + matched + ", changed " + changed
                + ", new " + added + ", gone " + removed;
        }

        private void Adopt(List<SettlementProfile> derived)
        {
            profiles = derived;
            observedSettlementCount = derived.Count;
            HashSet<int> regions = new HashSet<int>();
            foreach (SettlementProfile profile in derived)
            {
                if (profile.RegionId != ProfileBuilder.UnaffiliatedRegion)
                {
                    regions.Add(profile.RegionId);
                }
            }
            regionCount = regions.Count;
        }

        public override void WorldComponentTick()
        {
            base.WorldComponentTick();

            int currentTick = Find.TickManager.TicksGame;
            if (lastProcessedTick < 0)
            {
                lastProcessedTick = currentTick;
                return;
            }

            // A day already begun is finished before another starts
            // (docs/82 section 3), a few phases per tick, so the day's
            // work is spread instead of landing in one frame.
            if (scheduler != null && !scheduler.DayComplete)
            {
                Advance();
                if (scheduler.DayComplete)
                {
                    CompleteDay();
                }
                return;
            }

            if (currentTick - lastProcessedTick >= TicksPerDay)
            {
                BeginDay();
            }
        }

        /// <summary>
        /// Start a day's work. The phases are the ported model's, in the
        /// laboratory's order; today the component owns no economy state
        /// to run them against, so the list is empty and a day completes
        /// at once. Filling it is the step that needs the model wired to
        /// the world, and the scheduler is already proved not to change
        /// what it runs (docs/83).
        /// </summary>
        private void BeginDay()
        {
            scheduler = new DayScheduler(BuildPhases());
            scheduler.BeginDay();
            dayCursor = scheduler.Cursor;
            phaseMillis.Clear();
            Advance();
            if (scheduler.DayComplete)
            {
                CompleteDay();
            }
        }

        /// <summary>
        /// Check what a person was previously asked to look at, and say
        /// what was found in a form that can be pasted and re-checked
        /// (docs/88 section 2). A fresh world skips the load-only checks
        /// rather than passing them, because a skip and a pass are not
        /// the same thing.
        /// </summary>
        private void RunSelfCheck(bool fromLoad)
        {
            selfCheck = new SelfCheckReport();
            selfCheck.Expect(
                "save schema",
                SaveText.Schema.ToString(),
                schemaVersion.ToString(),
                "schema 4 carries the docked economy; 3 and below do not");

            if (!fromLoad)
            {
                selfCheck.Add("reload determinism", "reproduced N/N", "fresh world",
                    CheckVerdict.Skipped, "nothing saved to compare");
                selfCheck.Add("mid-day resume", "the saved cursor", "fresh world",
                    CheckVerdict.Skipped);
                selfCheck.Add("old save loads clean", "no economy state", "fresh world",
                    CheckVerdict.Skipped);
            }
            else
            {
                bool upgraded = schemaOnLoad >= 0 && schemaOnLoad < SaveText.Schema;

                // A save with no profiles node -- schema 1, or a world
                // saved before any were derived -- has nothing to compare
                // against. That is a case the check does not apply to, so
                // it skips: reporting it as a failure is the same error as
                // reporting it as a pass (docs/88 s5.2), and running the
                // component found it where reasoning had not (docs/91 s3).
                if (determinismStatus == "nothing saved to compare")
                {
                    selfCheck.Add(
                        "reload determinism",
                        "reproduced N/N",
                        determinismStatus,
                        CheckVerdict.Skipped,
                        "the save carried no profiles to compare against");
                }
                else
                {
                    // The exact sentence `CompareWithLoaded` returns when
                    // everything reproduced. Spelled once, here, because
                    // the first version omitted " on reload" and reported
                    // a perfect reload as a failure (docs/91 s3).
                    selfCheck.Expect(
                        "reload determinism",
                        "reproduced " + observedSettlementCount + "/"
                            + observedSettlementCount + " on reload",
                        determinismStatus,
                        "a mismatch means the derivation reads state that is not in the save");
                }

                // Decided once, at load, and reused: see `resumeCheck`.
                if (resumeCheck == null)
                {
                    resumeCheck = new Check();
                    resumeCheck.Name = "mid-day resume";
                    if (upgraded)
                    {
                        resumeCheck.Expected = "cursor 0 after a schema upgrade";
                        resumeCheck.Observed = "cursor " + dayCursor;
                        resumeCheck.Verdict = dayCursor == 0
                            ? CheckVerdict.Passed : CheckVerdict.Failed;
                        resumeCheck.Note = "a pre-schema-4 save carries no day to resume";
                    }
                    else
                    {
                        resumeCheck.Expected = "cursor " + cursorOnLoad;
                        resumeCheck.Observed =
                            scheduler == null ? "cursor 0" : "cursor " + scheduler.Cursor;
                        resumeCheck.Verdict =
                            resumeCheck.Expected == resumeCheck.Observed
                                ? CheckVerdict.Passed : CheckVerdict.Failed;
                        resumeCheck.Note =
                            "re-running a phase is not harmless: the settlement pays a wage bill";
                    }
                }
                selfCheck.Add(
                    resumeCheck.Name, resumeCheck.Expected, resumeCheck.Observed,
                    resumeCheck.Verdict, resumeCheck.Note);
                if (upgraded)
                {
                    selfCheck.Expect(
                        "old save loads clean",
                        "no economy state",
                        economyState.Length == 0 ? "no economy state" : "state present",
                        "a schema-" + schemaOnLoad + " save must not be read as schema 4");
                }
                else
                {
                    selfCheck.Add("old save loads clean", "no economy state",
                        "save was already schema " + schemaOnLoad, CheckVerdict.Skipped);
                }
            }

            if (economyFailure != null)
            {
                selfCheck.Add("docked economy", "running", economyFailure, CheckVerdict.Failed,
                    "the economy stopped rather than run a model that did not dock");
            }
            else if (economy == null)
            {
                selfCheck.Add("docked economy", "running",
                    regionCount == 0 ? "no faction region yet" : "not built yet", CheckVerdict.Skipped);
            }
            else
            {
                selfCheck.Add("docked economy", "running", EconomyStatus, CheckVerdict.Passed);
            }

            if (phaseMillis.Count > 0)
            {
                selfCheck.Add("tick budget", "measured",
                    TickBudget.Describe(phaseMillis, TickBudget.DefaultBudgetMs),
                    TickBudget.BudgetUnreachable(phaseMillis, TickBudget.DefaultBudgetMs)
                        ? CheckVerdict.Failed : CheckVerdict.Passed,
                    "PhasesPerTick is " + PhasesPerTick + " and was a guess until this ran");
            }
            else
            {
                selfCheck.Add("tick budget", "measured", "no day has run yet",
                    CheckVerdict.Skipped);
            }
        }

        /// <summary>
        /// One tick's worth of the day, timed.
        ///
        /// The clock lives here and not in the scheduler, which must stay
        /// free of it to be deterministic (docs/82 section 3). What the
        /// clock is for is `TickBudget`: `PhasesPerTick` is a guess until
        /// a real day has been timed, and this is what turns it into a
        /// measurement the self-check reports.
        /// </summary>
        private void Advance()
        {
            Stopwatch clock = Stopwatch.StartNew();
            int ran = scheduler.AdvanceTick(PhasesPerTick);
            clock.Stop();
            dayCursor = scheduler.Cursor;
            if (ran > 0)
            {
                double each = clock.Elapsed.TotalMilliseconds / ran;
                for (int i = 0; i < ran; i++)
                {
                    phaseMillis.Add(each);
                }
            }
        }

        private void CompleteDay()
        {
            // The day is timed, so the budget stops being a guess. Re-run
            // the checks with the measurement in hand, in the same posture
            // the world loaded in.
            RunSelfCheck(loadedFromSave);
            StepDay();
            lastProcessedTick += TicksPerDay;
            dayCursor = 0;
        }

        /// <summary>
        /// The day: the profiles, then the economy's own phases in the
        /// laboratory's order (docs/143 s2). The list is the same whether
        /// or not the economy exists yet, so a save taken mid-day resumes
        /// at the same phase: the build phase does nothing once built, and
        /// the docked phases do nothing until it has.
        /// </summary>
        private List<IDayPhase> BuildPhases()
        {
            List<IDayPhase> phases = new List<IDayPhase>();
            phases.Add(new DayPhase("profiles", delegate
            {
                Adopt(ProfileBuilder.Build());
            }));
            phases.Add(new DayPhase("economy", delegate
            {
                EnsureEconomy();
            }));
            foreach (DockedDay.Phase docked in DockedDay.Order)
            {
                System.Action<EconomyState> run = docked.Run;
                phases.Add(new DayPhase(docked.Name, delegate
                {
                    if (economy != null && economyFailure == null)
                    {
                        run(economy);
                    }
                }));
            }
            return phases;
        }

        /// <summary>
        /// Build the docked economy once the world has a faction region,
        /// and refuse a day the docked configuration does not cover
        /// (docs/141 s2). A refusal stops the economy and says why; it
        /// never runs a different model.
        /// </summary>
        private void EnsureEconomy()
        {
            if (economyFailure != null)
            {
                return;
            }
            try
            {
                if (economy == null)
                {
                    if (regionCount == 0)
                    {
                        return;
                    }
                    int seed = Find.World != null && Find.World.info != null
                        ? Find.World.info.persistentRandomValue
                        : 0;
                    economy = DockedDay.Build(seed, Commodities, regionCount);
                    Log.Message("[Social Production: Economy] Built the docked economy: "
                        + regionCount + " regions, " + Commodities + " commodities, seed " + seed + ".");
                }
                DockedDay.Refuse(economy);
            }
            catch (System.Exception failure)
            {
                economyFailure = failure.GetType().Name + ": " + failure.Message;
                Log.Error("[Social Production: Economy] The docked economy stopped: " + economyFailure);
            }
        }

        /// <summary>What the tab shows: each region's consumer goods, in
        /// units a player has (docs/94).</summary>
        private void RefreshReadouts()
        {
            readouts = new List<RegionReadout>();
            if (economy == null)
            {
                return;
            }
            Dictionary<string, double> values = ToDictionary(economy.LaborValues);
            for (int r = 0; r < economy.Regions.Count; r++)
            {
                Region region = economy.Regions.ValueAt(r);
                Dictionary<string, double> prices = new Dictionary<string, double>();
                for (int i = 0; i < region.BaseDailyDemand.Count; i++)
                {
                    string name = region.BaseDailyDemand.KeyAt(i);
                    prices[name] = region.Prices.Get(name, 0.0);
                }
                for (int i = 0; i < region.SubsistenceBasket.Count; i++)
                {
                    string name = region.SubsistenceBasket.KeyAt(i);
                    prices[name] = region.Prices.Get(name, 0.0);
                }
                Dictionary<string, double> output = new Dictionary<string, double>();
                foreach (Producer producer in region.Producers)
                {
                    double before;
                    output.TryGetValue(producer.Commodity, out before);
                    output[producer.Commodity] = before
                        + producer.LastRuns * producer.Process.Outputs.Get(producer.Commodity, 0.0);
                }
                double living = economy.Ledger.LivingLabor.Get(region.Name, 0.0);
                double necessary = economy.Ledger.NecessaryLabor.Get(region.Name, 0.0);
                readouts.Add(EconomyReadout.Build(
                    region.Name, values, prices, new Dictionary<string, double>(), output,
                    region.TicksPerWorkerDay, Lab.WageRate(region), necessary, living - necessary,
                    region.WorkerDaysEarned));
            }
        }

        private static Dictionary<string, double> ToDictionary(OrderedMap<double> map)
        {
            Dictionary<string, double> copy = new Dictionary<string, double>();
            for (int i = 0; i < map.Count; i++)
            {
                copy[map.KeyAt(i)] = map.ValueAt(i);
            }
            return copy;
        }

        public override void ExposeData()
        {
            base.ExposeData();
            if (Scribe.mode == LoadSaveMode.Saving)
            {
                // The whole economy as one string, in the format of
                // docs/143: doubles as their bits, never as decimal.
                economyState = economy == null ? "" : SaveText.Write(economy);
            }
            Scribe_Values.Look(ref schemaVersion, "schemaVersion", SaveSchemaVersion);
            Scribe_Values.Look(ref completedDays, "completedDays", 0);
            Scribe_Values.Look(ref lastProcessedTick, "lastProcessedTick", -1);
            Scribe_Values.Look(ref observedSettlementCount, "observedSettlementCount", 0);
            Scribe_Collections.Look(ref profiles, "profiles", LookMode.Deep);
            // The economy as one encoded string, never as loose doubles
            // (docs/81 section 3): a float must not cross an
            // implementation boundary as decimal, and a save file is such
            // a boundary the moment the writing and reading runtimes are
            // not guaranteed to be the same.
            Scribe_Values.Look(ref economyState, "economyState", "");
            Scribe_Values.Look(ref dayCursor, "dayCursor", 0);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                // Remembered before the upgrade below rewrites them, so
                // the self-check can say what the save actually carried.
                schemaOnLoad = schemaVersion;
                cursorOnLoad = dayCursor;
                if (profiles == null)
                {
                    // A save written by schema 1 has no profiles node at all.
                    profiles = new List<SettlementProfile>();
                }
                if (economyState == null)
                {
                    economyState = "";
                }
                if (schemaVersion < SaveText.Schema)
                {
                    // Schema 3 and earlier carry no docked economy. Start
                    // one rather than read fields that are not there.
                    economyState = "";
                    dayCursor = 0;
                    schemaVersion = SaveText.Schema;
                }
                else
                {
                    if (economyState.Length > 0)
                    {
                        try
                        {
                            economy = SaveText.Read(economyState);
                        }
                        catch (System.Exception failure)
                        {
                            economy = null;
                            economyFailure = "the saved economy did not decode: " + failure.Message;
                            Log.Error("[Social Production: Economy] " + economyFailure);
                        }
                    }
                    if (dayCursor > 0)
                    {
                        // A save taken mid-day resumes mid-day: the phases
                        // already applied are not applied again (docs/83 s3).
                        scheduler = new DayScheduler(BuildPhases());
                        scheduler.ResumeAt(dayCursor);
                    }
                }
                RefreshReadouts();
            }
        }

        private void StepDay()
        {
            completedDays++;
            Adopt(ProfileBuilder.Build());
            RefreshReadouts();
        }
    }
}
