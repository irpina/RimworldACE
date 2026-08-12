using RimWorld.Planet;
using Verse;

namespace SocialProduction.Economy
{
    public sealed class EconomyWorldComponent : WorldComponent
    {
        private const int TicksPerDay = 60000;
        private const int SaveSchemaVersion = 1;

        private int schemaVersion = SaveSchemaVersion;
        private int completedDays;
        private int lastProcessedTick = -1;
        private int observedSettlementCount;

        public EconomyWorldComponent(World world) : base(world)
        {
        }

        public int CompletedDays => completedDays;

        public int ObservedSettlementCount => observedSettlementCount;

        public override void FinalizeInit(bool fromLoad)
        {
            base.FinalizeInit(fromLoad);
            ObserveWorld();

            if (lastProcessedTick < 0 && Find.TickManager != null)
            {
                lastProcessedTick = Find.TickManager.TicksGame;
            }

            Log.Message("[Social Production: Economy] Read-only Stage 1 component initialized; vanilla trade prices are unchanged.");
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
        }

        private void StepDay()
        {
            completedDays++;
            ObserveWorld();
        }

        private void ObserveWorld()
        {
            observedSettlementCount = Find.WorldObjects == null
                ? 0
                : Find.WorldObjects.Settlements.Count;
        }
    }
}
