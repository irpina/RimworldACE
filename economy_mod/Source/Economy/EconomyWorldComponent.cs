using System.Collections.Generic;
using RimWorld.Planet;
using Verse;

namespace SocialProduction.Economy
{
    public sealed class EconomyWorldComponent : WorldComponent
    {
        private const int TicksPerDay = 60000;
        private const int SaveSchemaVersion = 2;

        private int schemaVersion = SaveSchemaVersion;
        private int completedDays;
        private int lastProcessedTick = -1;
        private int observedSettlementCount;
        private List<SettlementProfile> profiles = new List<SettlementProfile>();
        private int regionCount;
        private string determinismStatus = "not checked";

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

            Log.Message(
                "[Social Production: Economy] Stage 1 read-only component ready: "
                + observedSettlementCount + " settlements in " + regionCount
                + " regions; determinism check: " + determinismStatus
                + ". Vanilla trade prices are unchanged.");
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

            while (currentTick - lastProcessedTick >= TicksPerDay)
            {
                StepDay();
                lastProcessedTick += TicksPerDay;
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref schemaVersion, "schemaVersion", SaveSchemaVersion);
            Scribe_Values.Look(ref completedDays, "completedDays", 0);
            Scribe_Values.Look(ref lastProcessedTick, "lastProcessedTick", -1);
            Scribe_Values.Look(ref observedSettlementCount, "observedSettlementCount", 0);
            Scribe_Collections.Look(ref profiles, "profiles", LookMode.Deep);
            if (Scribe.mode == LoadSaveMode.PostLoadInit && profiles == null)
            {
                // A save written by schema 1 has no profiles node at all.
                profiles = new List<SettlementProfile>();
            }
        }

        private void StepDay()
        {
            completedDays++;
            Adopt(ProfileBuilder.Build());
        }
    }
}
