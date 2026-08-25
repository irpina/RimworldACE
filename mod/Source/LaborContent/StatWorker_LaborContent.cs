using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace SocialProduction.LaborContent
{
    /// <summary>
    /// Renders an embodied-labor stat in several units at once.
    ///
    /// The stat's stored value is work-seconds, RimWorld's own work unit
    /// (a recipe's workAmount divided by 60). Embodied labor across the
    /// 543 patched defs spans five orders of magnitude — under a second
    /// for a chunk of steel, thousands for a bionic — so no single unit
    /// reads well everywhere: seconds are unreadable at the top of the
    /// range and hours are all zeroes at the bottom.
    ///
    /// XML cannot fix that. StatDef.formatString takes exactly one value
    /// and cannot compute a second, which is why this mod carries an
    /// assembly at all. It is the only reason it does: no Harmony, no
    /// patching, no gameplay or save effect, and one virtual method.
    ///
    /// The units are all exact and none of them is a convention:
    ///   1 work-second  = 60 ticks (GenText.ToStringWorkAmount's divisor)
    ///   1 in-game hour = 2,500 ticks
    /// Deliberately absent is any "colonist-day", which would need an
    /// assumption about how much of a day a colonist works.
    ///
    /// A unit is shown only where it says something, and at most two are
    /// shown so the line cannot wrap. A steel bar reads "48 ticks" rather
    /// than "0.019 in-game h · 0.79 work-s · 48 ticks", because at that
    /// magnitude the coarse units are noise; a rifle reads "10.8 in-game h
    /// · 450 work-s" and drops the ticks, which are the least useful unit
    /// once a thing is big enough to have hours.
    /// </summary>
    public class StatWorker_LaborContent : StatWorker
    {
        private const float TicksPerWorkSecond = 60f;
        private const float TicksPerInGameHour = 2500f;

        private static StatDef extractionStat;
        private static StatDef workToMakeStat;
        private static StatDef workToBuildStat;
        private static bool statsResolved;

        private static void ResolveStats()
        {
            if (statsResolved)
            {
                return;
            }
            statsResolved = true;
            extractionStat = DefDatabase<StatDef>.GetNamedSilentFail(
                "SNLT_ExtractionLabor");
            workToMakeStat = DefDatabase<StatDef>.GetNamedSilentFail(
                "WorkToMake");
            workToBuildStat = DefDatabase<StatDef>.GetNamedSilentFail(
                "WorkToBuild");
        }

        /// <summary>
        /// Add the labor in the stuff the thing is actually made of.
        ///
        /// The patches ship a *stuff-free* base, because the offline solver
        /// treats stuff as a substitutable input and picks the cheapest —
        /// so a knife's solved figure is obsidian's, and a plasteel knife
        /// would otherwise report material costs 6.7x too low. statBases
        /// has no notion of stuff, so the arithmetic has to happen here.
        ///
        /// Only extraction is stuff-dependent: fabrication is the thing's
        /// own work, which the solver already reports stuff-free. Stuffs
        /// are not themselves stuffable, so reading a stuff's own
        /// extraction labor cannot recurse.
        /// </summary>
        public override float GetValueUnfinalized(
            StatRequest req, bool applyPostProcess)
        {
            float value = base.GetValueUnfinalized(req, applyPostProcess);
            ResolveStats();
            ThingDef stuff = req.StuffDef;
            ThingDef thing = req.Def as ThingDef;
            if (stuff == null || thing == null)
            {
                return value;
            }

            if (stat == extractionStat)
            {
                // The material the thing is actually made of.
                if (thing.costStuffCount <= 0)
                {
                    return value;
                }
                return value
                    + thing.costStuffCount
                        * stuff.GetStatValueAbstract(extractionStat);
            }

            // Fabrication: RimWorld scales the work itself by the stuff, so
            // a plasteel knife really does take 2.2x the labor of a steel
            // one. Leaving this unscaled while extraction *is* stuff-aware
            // would make the two rows disagree with each other and with
            // "Work to make" three lines above them.
            StatDef workStat = WorkStatFor(thing);
            if (workStat == null
                || stuff.stuffProps == null
                || stuff.stuffProps.statFactors == null)
            {
                return value;
            }
            return value * StatUtility.GetStatFactorFromList(
                stuff.stuffProps.statFactors, workStat);
        }

        /// <summary>
        /// Which work stat this thing's fabrication labor was measured in.
        ///
        /// The offline solver takes whichever of WorkToMake and WorkToBuild
        /// the def declares, so the stuff factor has to be read from the
        /// same one or a stuffed wall would be scaled by a factor meant for
        /// a weapon.
        /// </summary>
        private static StatDef WorkStatFor(ThingDef thing)
        {
            if (workToMakeStat != null
                && StatUtility.StatListContains(thing.statBases, workToMakeStat))
            {
                return workToMakeStat;
            }
            if (workToBuildStat != null
                && StatUtility.StatListContains(thing.statBases, workToBuildStat))
            {
                return workToBuildStat;
            }
            return null;
        }

        /// <summary>
        /// Decide visibility ourselves, because the base cannot.
        ///
        /// StatWorker.ShouldShowFor is a chain of equality tests against
        /// hardcoded StatCategoryDefOf members and falls through to
        /// Log.Error("Unhandled case: ...") plus `return false` for any
        /// category it does not recognise. So a *custom* StatCategoryDef —
        /// which is what puts these two stats in their own info-card
        /// section — cannot work unless the worker owns this method too.
        ///
        /// The rule is simply: show the stat on things that carry it. The
        /// patches write it onto exactly the 543 defs it was solved for,
        /// so membership in statBases is the whole question.
        /// </summary>
        public override bool ShouldShowFor(StatRequest req)
        {
            if (stat.alwaysHide)
            {
                return false;
            }
            if (!stat.CanShowWithLoadedMods())
            {
                return false;
            }
            if (stat.showIfUndefined)
            {
                return req.Def is ThingDef;
            }
            return StatUtility.StatListContains(req.StatBases, stat);
        }

        public override string ValueToString(
            float val, bool finalized, ToStringNumberSense numberSense)
        {
            // Offsets and factors are relative quantities; a multi-unit
            // rendering of "+3" would be nonsense. Only the absolute
            // reading gets the treatment.
            if (numberSense != ToStringNumberSense.Absolute)
            {
                return base.ValueToString(val, finalized, numberSense);
            }
            if (val <= 0f)
            {
                return "0";
            }

            float ticks = val * TicksPerWorkSecond;
            float hours = ticks / TicksPerInGameHour;

            // Every unit from the coarsest useful one down to ticks. A unit
            // below 1 is dropped from the front rather than printed as a
            // leading zero-point-something.
            List<string> parts = new List<string>(2);
            if (hours >= 1f)
            {
                parts.Add(Readable(hours) + " in-game h");
            }
            if (val >= 1f)
            {
                parts.Add(Readable(val) + " work-s");
            }
            // At most two. Three wrapped onto a second row on a bolt-action
            // rifle at 1080p, and the unit that gets dropped is always the
            // least useful one present: ticks, when the thing is big enough
            // to have hours. Ticks still appear on their own for small
            // things, which is exactly when they are the readable unit.
            if (parts.Count < 2)
            {
                parts.Add(Readable(ticks) + " ticks");
            }
            // Escaped rather than literal: without a byte-order mark
            // csc reads source in the ANSI codepage, and a middle dot
            // would arrive in the assembly as mojibake.
            return string.Join(" · ", parts.ToArray());
        }

        /// <summary>
        /// Enough significant figures to be useful, and no more.
        ///
        /// A fixed number of decimals would print "0.00" for a chunk of
        /// steel and "8040.00" for a parka; the precision has to follow
        /// the magnitude.
        /// </summary>
        private static string Readable(float value)
        {
            if (value >= 100f)
            {
                return value.ToString("N0");
            }
            if (value >= 10f)
            {
                return value.ToString("0.#");
            }
            if (value >= 1f)
            {
                return value.ToString("0.##");
            }
            return value.ToString("0.###");
        }
    }
}
