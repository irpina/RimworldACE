using System.Collections.Generic;
using System.Diagnostics;
using RimWorld.Planet;
using SocialProduction.Economy.Core;
using Verse;

namespace SocialProduction.Economy
{
    public sealed class EconomyWorldComponent : WorldComponent
    {
        private const int TicksPerDay = 60000;

        /// <summary>
        /// Schema 2 is the profiles-only shell. Economy state is schema 3
        /// (docs/80 section 2): a schema-2 save must load with no economy
        /// rather than read its fields as something they are not.
        /// </summary>
        private const int SaveSchemaVersion = StateCodec.SchemaVersion;

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
                StateCodec.SchemaVersion.ToString(),
                schemaVersion.ToString(),
                "schema 3 carries economy state; 2 and below do not");

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
                bool upgraded = schemaOnLoad >= 0 && schemaOnLoad < StateCodec.SchemaVersion;

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

                // An upgraded save had its cursor deliberately reset, so
                // there is no resume to check -- expecting the old value
                // would report the upgrade working as a failure.
                if (upgraded)
                {
                    selfCheck.Add(
                        "mid-day resume",
                        "cursor 0 after a schema upgrade",
                        "cursor " + dayCursor,
                        dayCursor == 0 ? CheckVerdict.Passed : CheckVerdict.Failed,
                        "a pre-schema-3 save carries no day to resume");
                }
                else
                {
                    selfCheck.Expect(
                        "mid-day resume",
                        "cursor " + cursorOnLoad,
                        scheduler == null ? "cursor 0" : "cursor " + scheduler.Cursor,
                        "re-running a phase is not harmless: the settlement pays a wage bill");
                }
                if (upgraded)
                {
                    selfCheck.Expect(
                        "old save loads clean",
                        "no economy state",
                        economyState.Length == 0 ? "no economy state" : "state present",
                        "a schema-" + schemaOnLoad + " save must not be read as schema 3");
                }
                else
                {
                    selfCheck.Add("old save loads clean", "no economy state",
                        "save was already schema " + schemaOnLoad, CheckVerdict.Skipped);
                }
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

        private List<IDayPhase> BuildPhases()
        {
            // One placeholder phase so the scheduler always has work and
            // the cursor means something. Replaced by the ported solvers
            // when the component carries an EconomySnapshot.
            List<IDayPhase> phases = new List<IDayPhase>();
            phases.Add(new DayPhase("profiles", delegate
            {
                Adopt(ProfileBuilder.Build());
            }));
            return phases;
        }

        public override void ExposeData()
        {
            base.ExposeData();
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
                if (schemaVersion < StateCodec.SchemaVersion)
                {
                    // Schema 2 and earlier carry no economy. Start one
                    // rather than read fields that are not there.
                    economyState = "";
                    dayCursor = 0;
                    schemaVersion = StateCodec.SchemaVersion;
                }
                else if (dayCursor > 0)
                {
                    // A save taken mid-day resumes mid-day: the phases
                    // already applied are not applied again (docs/83 s3).
                    scheduler = new DayScheduler(BuildPhases());
                    scheduler.ResumeAt(dayCursor);
                }
            }
        }

        private void StepDay()
        {
            completedDays++;
            Adopt(ProfileBuilder.Build());
        }
    }
}
