using System.Collections.Generic;

namespace Verse
{
    /// <summary>
    /// Enough host behaviour to *drive* the mod, not only compile it
    /// (docs/90).
    ///
    /// RimWorld's contribution to the mod's state machine is plumbing: a
    /// tick counter, a `Scribe` that stores a value under a label and
    /// hands it back, and a world that lists settlements. None of it is
    /// interesting, and all of it can be faked — which turns "the wiring
    /// compiles" into "the wiring runs and does the right thing given a
    /// host that behaves as documented".
    ///
    /// **This is not a claim about RimWorld.** It says nothing about
    /// whether the real `Scribe` behaves like this one, when
    /// `FinalizeInit` is really called, or anything at all about
    /// rendering. It tests the half of the remaining risk that is the
    /// mod's fault if it is wrong. Never shipped.
    /// </summary>
    public static class FakeHost
    {
        private static readonly Dictionary<string, object> store =
            new Dictionary<string, object>();

        public static TickManager Ticks = new TickManager();
        public static int TicksGame;

        public static RimWorld.Planet.World World = new RimWorld.Planet.World();
        public static RimWorld.Planet.WorldObjectsHolder WorldObjects =
            new RimWorld.Planet.WorldObjectsHolder();
        public static RimWorld.Planet.WorldGrid WorldGrid = new RimWorld.Planet.WorldGrid();

        /// <summary>
        /// Populate a world, so the profile derivation and with it the
        /// reload-determinism check are actually exercised. Without
        /// settlements the check legitimately skips, which is correct
        /// behaviour and tests nothing.
        /// </summary>
        public static void Populate(int settlements)
        {
            World = new RimWorld.Planet.World();
            World.info = new RimWorld.Planet.WorldInfo();
            World.info.persistentRandomValue = 12345;
            WorldObjects = new RimWorld.Planet.WorldObjectsHolder();
            WorldGrid = new RimWorld.Planet.WorldGrid();
            RimWorld.BiomeDef biome = new RimWorld.BiomeDef();
            biome.defName = "TemperateForest";
            for (int i = 0; i < settlements; i++)
            {
                RimWorld.Faction faction = new RimWorld.Faction();
                faction.FakeName = "Faction " + (i % 3);
                faction.loadID = i % 3;
                RimWorld.Planet.Settlement settlement = new RimWorld.Planet.Settlement();
                settlement.ID = 1000 + i;
                settlement.FakeTile = new RimWorld.Planet.PlanetTile();
                settlement.FakeTile.tileId = 500 + i;
                settlement.FakeFaction = faction;
                WorldObjects.FakeSettlements.Add(settlement);
                RimWorld.Planet.Tile tile = new RimWorld.Planet.Tile();
                tile.FakeBiome = biome;
                tile.hilliness = RimWorld.Planet.Hilliness.SmallHills;
                WorldGrid.Tiles[settlement.FakeTile.tileId] = tile;
            }
        }

        /// <summary>Forget the save file and the clock, between scenarios.</summary>
        public static void Reset()
        {
            store.Clear();
            TicksGame = 0;
            Scribe.mode = LoadSaveMode.Inactive;
            Populate(0);
        }

        /// <summary>Keep the saved values but start a new component: a reload.</summary>
        public static void KeepSaveResetClock()
        {
            TicksGame = 0;
        }

        public static void ScribeValue<T>(ref T value, string label, T defaultValue)
        {
            switch (Scribe.mode)
            {
                case LoadSaveMode.Saving:
                    store[label] = value;
                    break;
                case LoadSaveMode.LoadingVars:
                    object saved;
                    value = store.TryGetValue(label, out saved) && saved is T
                        ? (T)saved
                        : defaultValue;
                    break;
            }
        }

        public static void ScribeList<T>(ref List<T> list, string label)
        {
            switch (Scribe.mode)
            {
                case LoadSaveMode.Saving:
                    store[label] = list == null ? null : new List<T>(list);
                    break;
                case LoadSaveMode.LoadingVars:
                    object saved;
                    list = store.TryGetValue(label, out saved) && saved is List<T>
                        ? new List<T>((List<T>)saved)
                        : null;
                    break;
            }
        }

        /// <summary>Rewrite one saved value, to fake a save from an older schema.</summary>
        public static void Poke(string label, object value)
        {
            store[label] = value;
        }

        public static bool Has(string label)
        {
            return store.ContainsKey(label);
        }

        public static object Peek(string label)
        {
            object saved;
            return store.TryGetValue(label, out saved) ? saved : null;
        }
    }
}
