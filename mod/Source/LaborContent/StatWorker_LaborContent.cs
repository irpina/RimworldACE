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
    /// A unit is shown only where it says something. A steel bar reads
    /// "48 ticks" rather than "0.019 in-game h · 0.79 work-s · 48
    /// ticks", because at that magnitude the coarse units are noise and
    /// leading with noise is worse than showing one unit.
    /// </summary>
    public class StatWorker_LaborContent : StatWorker
    {
        private const float TicksPerWorkSecond = 60f;
        private const float TicksPerInGameHour = 2500f;

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
            List<string> parts = new List<string>(3);
            if (hours >= 1f)
            {
                parts.Add(Readable(hours) + " in-game h");
            }
            if (val >= 1f)
            {
                parts.Add(Readable(val) + " work-s");
            }
            parts.Add(Readable(ticks) + " ticks");
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
