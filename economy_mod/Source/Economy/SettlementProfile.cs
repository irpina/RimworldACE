using Verse;

namespace SocialProduction.Economy
{
    /// <summary>
    /// One settlement's economic identity, derived rather than invented.
    ///
    /// Everything here except <see cref="Fingerprint"/> is read off the world
    /// the game generated: which faction holds the settlement, which tile it
    /// sits on, and what that tile is. Nothing is rolled, because a roll
    /// would have to come from <c>Rand</c>, and <c>Rand</c> is global mutable
    /// state shared with the game's own generation — drawing from it would
    /// make this component's output depend on how many other things happened
    /// to draw first.
    ///
    /// <see cref="Fingerprint"/> is a pure function of the world's
    /// <c>persistentRandomValue</c> and the tile id, so two settlements on
    /// one tile of one world always get the same value and the same
    /// settlement on a regenerated world does not. It is the hook a later
    /// stage will hang per-settlement variation on; nothing reads it yet.
    /// </summary>
    public sealed class SettlementProfile : IExposable
    {
        private int settlementId;
        private int tileId;
        private int regionId;
        private string factionName;
        private string biome;
        private string hilliness;
        private int fingerprint;

        public SettlementProfile()
        {
        }

        public SettlementProfile(
            int settlementId,
            int tileId,
            int regionId,
            string factionName,
            string biome,
            string hilliness,
            int fingerprint)
        {
            this.settlementId = settlementId;
            this.tileId = tileId;
            this.regionId = regionId;
            this.factionName = factionName;
            this.biome = biome;
            this.hilliness = hilliness;
            this.fingerprint = fingerprint;
        }

        public int SettlementId => settlementId;

        public int TileId => tileId;

        public int RegionId => regionId;

        public string FactionName => factionName;

        public string Biome => biome;

        public string Hilliness => hilliness;

        public int Fingerprint => fingerprint;

        /// <summary>
        /// Whether two profiles agree in every derived field.
        ///
        /// Used to compare a reloaded profile against a freshly derived one.
        /// A disagreement means something in the derivation is not a pure
        /// function of the saved world, which is the failure this whole
        /// design exists to make visible.
        /// </summary>
        public bool Matches(SettlementProfile other)
        {
            return other != null
                && settlementId == other.settlementId
                && tileId == other.tileId
                && regionId == other.regionId
                && factionName == other.factionName
                && biome == other.biome
                && hilliness == other.hilliness
                && fingerprint == other.fingerprint;
        }

        public string Describe()
        {
            return "settlement " + settlementId
                + " tile " + tileId
                + " region " + regionId
                + " faction " + (factionName ?? "none")
                + " biome " + (biome ?? "none")
                + " hilliness " + (hilliness ?? "none")
                + " fingerprint " + fingerprint;
        }

        public void ExposeData()
        {
            Scribe_Values.Look(ref settlementId, "settlementId", 0);
            Scribe_Values.Look(ref tileId, "tileId", 0);
            Scribe_Values.Look(ref regionId, "regionId", 0);
            Scribe_Values.Look(ref factionName, "factionName");
            Scribe_Values.Look(ref biome, "biome");
            Scribe_Values.Look(ref hilliness, "hilliness");
            Scribe_Values.Look(ref fingerprint, "fingerprint", 0);
        }
    }
}
