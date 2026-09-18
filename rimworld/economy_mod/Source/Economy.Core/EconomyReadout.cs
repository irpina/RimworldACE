using System;
using System.Collections.Generic;
using System.Globalization;

namespace SocialProduction.Economy.Core
{
    /// <summary>One commodity, in units a player has (docs/94 section 1).</summary>
    public sealed class ReadoutRow
    {
        public string Commodity = "";
        /// <summary>Labour to reproduce one unit, in worker-days.</summary>
        public double ValueWorkerDays;
        /// <summary>Silver.</summary>
        public double Price;
        /// <summary>
        /// Price over value, both in silver per worker-day: a pure number,
        /// exactly 1.0 where a commodity's price equals its value at the
        /// region's own wage. **The number this mod exists to show.**
        /// Negative means it could not be computed.
        /// </summary>
        public double PriceOverValue = -1.0;
        /// <summary>Differential rent as a share of the sector's value.</summary>
        public double RentShare;
    }

    /// <summary>One region's economy, as a tab would print it.</summary>
    public sealed class RegionReadout
    {
        public string Region = "";
        public double WagePerDay;
        /// <summary>Surplus over necessary labour: an outcome, not an input (docs/20).</summary>
        public double RateOfSurplusValue = -1.0;
        public double WorkerDaysEarned;
        public List<ReadoutRow> Rows = new List<ReadoutRow>();
    }

    /// <summary>
    /// Turn the model's state into something legible (docs/94).
    ///
    /// Not a dump. The model's quantities are in work-ticks and raw
    /// ledger sums, which are the right units to compute in and the wrong
    /// ones to read: a value of 735.975 ticks says nothing, and 0.031
    /// worker-days is a sentence. Four deliberate conversions — worker-
    /// days for ticks, price over value for the two separately, a rate of
    /// surplus value for three labour sums, and rent as a share for a
    /// silver total.
    ///
    /// Every reading is defensive, because the failure mode a panel like
    /// this has is not crashing: it is printing `NaN` with the authority
    /// of a measurement.
    /// </summary>
    public static class EconomyReadout
    {
        private const double Epsilon = 1e-9;

        public static RegionReadout Build(
            string region,
            IDictionary<string, double> laborValues,
            IDictionary<string, double> prices,
            IDictionary<string, double> rentByCommodity,
            IDictionary<string, double> outputByCommodity,
            double ticksPerWorkerDay,
            double wagePerDay,
            double necessaryLabor,
            double surplusLabor,
            double workerDaysEarned)
        {
            RegionReadout readout = new RegionReadout();
            readout.Region = region ?? "";
            readout.WagePerDay = Usable(wagePerDay) ? wagePerDay : 0.0;
            readout.WorkerDaysEarned = Usable(workerDaysEarned) ? workerDaysEarned : 0.0;
            readout.RateOfSurplusValue =
                Usable(necessaryLabor) && Usable(surplusLabor) && necessaryLabor > Epsilon
                    ? surplusLabor / necessaryLabor
                    : -1.0;

            List<string> names = new List<string>();
            if (prices != null)
            {
                foreach (KeyValuePair<string, double> entry in prices) names.Add(entry.Key);
            }
            names.Sort(StringComparer.Ordinal);

            foreach (string name in names)
            {
                ReadoutRow row = new ReadoutRow();
                row.Commodity = name;

                double price;
                row.Price = prices.TryGetValue(name, out price) && Usable(price) ? price : 0.0;

                double ticks = 0.0;
                if (laborValues != null)
                {
                    laborValues.TryGetValue(name, out ticks);
                }
                bool valued = Usable(ticks) && ticks > Epsilon
                    && Usable(ticksPerWorkerDay) && ticksPerWorkerDay > Epsilon;
                row.ValueWorkerDays = valued ? ticks / ticksPerWorkerDay : 0.0;

                // Both sides in silver per worker-day, so the ratio is a
                // pure number and cannot depend on how long a tick is.
                if (valued && readout.WagePerDay > Epsilon)
                {
                    double valueInSilver = row.ValueWorkerDays * readout.WagePerDay;
                    row.PriceOverValue = valueInSilver > Epsilon
                        ? row.Price / valueInSilver
                        : -1.0;
                    if (!Usable(row.PriceOverValue)) row.PriceOverValue = -1.0;
                }

                double rent = 0.0;
                if (rentByCommodity != null) rentByCommodity.TryGetValue(name, out rent);
                double output = 0.0;
                if (outputByCommodity != null) outputByCommodity.TryGetValue(name, out output);
                double sectorValue = Usable(output) && output > Epsilon
                    ? output * row.Price
                    : 0.0;
                row.RentShare = Usable(rent) && sectorValue > Epsilon
                    ? rent / sectorValue
                    : 0.0;
                if (!Usable(row.RentShare)) row.RentShare = 0.0;

                readout.Rows.Add(row);
            }
            return readout;
        }

        /// <summary>A number a player reads, never NaN and never infinity.</summary>
        public static string Number(double value, int places = 3)
        {
            if (!Usable(value))
            {
                return "n/a";
            }
            return value.ToString("0." + new string('#', Math.Max(places, 1)),
                CultureInfo.InvariantCulture);
        }

        /// <summary>A ratio, with the sentinel spelled rather than printed.</summary>
        public static string Ratio(double value)
        {
            return value < 0.0 ? "n/a" : Number(value) + "x";
        }

        public static string Percent(double share)
        {
            return !Usable(share) ? "n/a" : Number(share * 100.0, 2) + "%";
        }

        /// <summary>The region's headline, for the tab's summary line.</summary>
        public static string Headline(RegionReadout readout)
        {
            return "wage " + Number(readout.WagePerDay) + " silver/day"
                + ", s/v " + Ratio(readout.RateOfSurplusValue)
                + ", employment " + Number(readout.WorkerDaysEarned)
                + " worker-days";
        }

        private static bool Usable(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }
    }
}
