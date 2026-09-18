using System.Collections.Generic;
using RimWorld;
using RimWorld.Planet;
using Verse;

namespace SocialProduction.Economy
{
    /// <summary>
    /// Derives settlement profiles and regional membership from the world.
    ///
    /// Two rules, both borrowed from the Stage 0 laboratory because they are
    /// what makes its histories reproducible:
    ///
    /// **Nothing is rolled.** No <c>Rand</c>, anywhere. Where variation is
    /// wanted it comes from hashing stable identity, so the answer does not
    /// depend on what else drew from the generator first.
    ///
    /// **Order is imposed, never inherited.** `Find.WorldObjects.Settlements`
    /// is in whatever order the world happens to hold it, and that order can
    /// change when a settlement is destroyed or added. Everything here sorts
    /// by tile id first, so region numbering is a function of the world and
    /// not of the list.
    /// </summary>
    public static class ProfileBuilder
    {
        /// <summary>Region assigned to a settlement no faction holds.</summary>
        public const int UnaffiliatedRegion = -1;

        public static List<SettlementProfile> Build()
        {
            List<SettlementProfile> profiles = new List<SettlementProfile>();
            if (Find.WorldObjects == null || Find.WorldGrid == null)
            {
                return profiles;
            }

            int worldSeed = Find.World != null && Find.World.info != null
                ? Find.World.info.persistentRandomValue
                : 0;

            List<Settlement> ordered = new List<Settlement>(
                Find.WorldObjects.Settlements);
            ordered.Sort(CompareByTile);

            // Region ids are assigned by a faction's first appearance in tile
            // order, so the numbering is stable for a given world rather than
            // depending on faction creation order.
            Dictionary<int, int> regionOfFaction = new Dictionary<int, int>();

            foreach (Settlement settlement in ordered)
            {
                if (settlement == null)
                {
                    continue;
                }
                int tileId = settlement.Tile.tileId;

                int regionId = UnaffiliatedRegion;
                string factionName = null;
                Faction faction = settlement.Faction;
                if (faction != null)
                {
                    factionName = faction.Name;
                    int key = faction.loadID;
                    if (!regionOfFaction.TryGetValue(key, out regionId))
                    {
                        regionId = regionOfFaction.Count;
                        regionOfFaction[key] = regionId;
                    }
                }

                string biome = null;
                string hilliness = null;
                Tile tile = Find.WorldGrid[settlement.Tile];
                if (tile != null)
                {
                    if (tile.PrimaryBiome != null)
                    {
                        biome = tile.PrimaryBiome.defName;
                    }
                    hilliness = tile.hilliness.ToString();
                }

                profiles.Add(
                    new SettlementProfile(
                        settlement.ID,
                        tileId,
                        regionId,
                        factionName,
                        biome,
                        hilliness,
                        Fingerprint(worldSeed, tileId)));
            }
            return profiles;
        }

        private static int CompareByTile(Settlement left, Settlement right)
        {
            if (left == null)
            {
                return right == null ? 0 : 1;
            }
            if (right == null)
            {
                return -1;
            }
            int byTile = left.Tile.tileId.CompareTo(right.Tile.tileId);
            // Two settlements cannot share a tile, but the id breaks the tie
            // rather than leaving the order of equal keys to the sort.
            return byTile != 0 ? byTile : left.ID.CompareTo(right.ID);
        }

        /// <summary>
        /// SplitMix64 finalizer over the world seed and the tile.
        ///
        /// The same mixer `economy_lab/scale.py` uses, for the same reason:
        /// it is a pure function, it is well distributed on small sequential
        /// inputs like tile ids, and it is short enough to be obviously
        /// deterministic. Returned as a signed int because that is what
        /// `Scribe_Values` round-trips without ceremony.
        /// </summary>
        public static int Fingerprint(int worldSeed, int tileId)
        {
            ulong z = unchecked(
                (ulong)(uint)worldSeed * 0x9E3779B97F4A7C15UL
                + (ulong)(uint)tileId);
            z = unchecked((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL);
            z = unchecked((z ^ (z >> 27)) * 0x94D049BB133111EBUL);
            z ^= z >> 31;
            return unchecked((int)(uint)(z & 0x7FFFFFFFUL));
        }
    }
}
