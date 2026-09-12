using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>How much, if at all, the model's prices reach colony wealth.</summary>
    public enum WealthMode
    {
        /// <summary>Nothing reaches wealth. The default, and provably inert.</summary>
        Observe = 0,
        /// <summary>A factor clamped to a band around 1.0. Opt-in, never default.</summary>
        Bounded = 1,
        /// <summary>The model's price, unclamped. Never shipped; exists to measure the danger.</summary>
        Unbounded = 2,
    }

    /// <summary>
    /// Keep a volatile price system away from the storyteller (docs/84).
    ///
    /// RimWorld scales threats to colony wealth and wealth sums
    /// <c>MarketValue</c>, which is static. A model whose price triples
    /// in a glut would make a colony that did nothing three times as
    /// rich, and the storyteller would send raids for a fortune the
    /// player never accumulated. The inverse is subtler and worse: a
    /// crash in a stockpiled good makes raids easier, which turns a
    /// market simulation into a difficulty slider.
    ///
    /// So the economy never writes <c>MarketValue</c>, and in the
    /// default mode contributes nothing to wealth at all. This class
    /// exists to make that a *checked* property rather than one that
    /// holds because nothing is wired yet, and to give a designer
    /// considering a coupling a number instead of an intuition.
    /// </summary>
    public static class WealthCoupling
    {
        /// <summary>
        /// What one unit contributes, as a multiple of its authored
        /// value. Exactly 1.0 in <see cref="WealthMode.Observe"/>, for
        /// every input — the default build cannot affect raids, and that
        /// is a claim the player is owed rather than a tendency.
        /// </summary>
        public static double Factor(
            WealthMode mode, double modelPrice, double authoredValue, double band)
        {
            if (mode == WealthMode.Observe)
            {
                return 1.0;
            }
            // An authored value of zero has no ratio to speak of, and a
            // non-finite model price is a bug upstream; neither may move
            // wealth, so both fall back to vanilla's own number.
            if (!IsUsable(modelPrice) || !IsUsable(authoredValue) || authoredValue <= 0.0)
            {
                return 1.0;
            }
            double raw = modelPrice / authoredValue;
            if (!IsUsable(raw))
            {
                return 1.0;
            }
            if (mode == WealthMode.Unbounded)
            {
                return raw;
            }
            // Bounded: a price that has tripled contributes at most the
            // band's edge. The clamp is the whole point of the mode.
            double safeBand = IsUsable(band) && band > 0.0 ? band : 0.0;
            double high = 1.0 + safeBand;
            double low = 1.0 / high;
            if (raw > high)
            {
                return high;
            }
            if (raw < low)
            {
                return low;
            }
            return raw;
        }

        /// <summary>
        /// The colony's wealth under this mode over its wealth under
        /// vanilla: the exposure, and the number to look at before
        /// enabling any coupling.
        ///
        /// Returns exactly 1.0 when there is nothing to weigh, so an
        /// empty colony is not reported as infinitely richer or poorer.
        /// </summary>
        public static double ProjectedWealthRatio(
            WealthMode mode,
            IEnumerable<Quantity> stocks,
            IDictionary<string, double> modelPrices,
            IDictionary<string, double> authoredValues,
            double band)
        {
            double vanilla = 0.0;
            double coupled = 0.0;
            foreach (Quantity stock in stocks)
            {
                double authored;
                if (!authoredValues.TryGetValue(stock.Name, out authored))
                {
                    continue;
                }
                // A negative stock is not a thing a colony can hold; it
                // would let one line cancel another and hide an excursion.
                double held = IsUsable(stock.Amount) && stock.Amount > 0.0
                    ? stock.Amount
                    : 0.0;
                if (!IsUsable(authored) || authored <= 0.0 || held <= 0.0)
                {
                    continue;
                }
                double model;
                if (!modelPrices.TryGetValue(stock.Name, out model))
                {
                    model = authored;
                }
                double value = held * authored;
                vanilla += value;
                coupled += value * Factor(mode, model, authored, band);
            }
            if (vanilla <= 0.0)
            {
                return 1.0;
            }
            return coupled / vanilla;
        }

        private static bool IsUsable(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }
    }
}
