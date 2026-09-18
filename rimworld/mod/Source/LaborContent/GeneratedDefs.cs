using System.Collections.Generic;
using RimWorld;
using Verse;

namespace SocialProduction.LaborContent
{
    /// <summary>One generated def's solved labor content.</summary>
    public class LaborContentEntry
    {
        public string defName;
        public float extraction;
        public float fabrication;
    }

    /// <summary>
    /// Labor content for defs that no patch can reach.
    ///
    /// RimWorld generates 104 meat defs at load from animal defs, so there
    /// is no XML node for a PatchOperation to target. They were a hard gap
    /// while the mod was XML-only. With an assembly present the fix is a
    /// table and a startup pass.
    ///
    /// The figures come from the same offline solve as everything else;
    /// this ships them rather than deriving them, so the numbers on a
    /// generated def and a patched one cannot drift apart.
    /// </summary>
    public class LaborContentTableDef : Def
    {
        public List<LaborContentEntry> entries = new List<LaborContentEntry>();
    }

    [StaticConstructorOnStartup]
    public static class LaborContentStartup
    {
        static LaborContentStartup()
        {
            StatDef extraction =
                DefDatabase<StatDef>.GetNamedSilentFail("SNLT_ExtractionLabor");
            StatDef fabrication =
                DefDatabase<StatDef>.GetNamedSilentFail("SNLT_FabricationLabor");
            if (extraction == null || fabrication == null)
            {
                Log.Error("[Labor Content] stat defs missing; generated defs "
                          + "will have no labor content.");
                return;
            }

            int applied = 0;
            int missing = 0;
            foreach (LaborContentTableDef table
                     in DefDatabase<LaborContentTableDef>.AllDefs)
            {
                foreach (LaborContentEntry entry in table.entries)
                {
                    ThingDef thing =
                        DefDatabase<ThingDef>.GetNamedSilentFail(entry.defName);
                    if (thing == null)
                    {
                        // A def from an expansion the player does not own.
                        // Expected, and not worth a warning each.
                        missing++;
                        continue;
                    }
                    if (thing.statBases == null)
                    {
                        thing.statBases = new List<StatModifier>();
                    }
                    thing.SetStatBaseValue(extraction, entry.extraction);
                    thing.SetStatBaseValue(fabrication, entry.fabrication);
                    applied++;
                }
            }
            Log.Message("[Labor Content] labor content applied to " + applied
                        + " generated defs (" + missing + " not present).");
        }
    }
}
