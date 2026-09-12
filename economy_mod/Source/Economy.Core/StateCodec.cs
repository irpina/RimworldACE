using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace SocialProduction.Economy.Core
{
    /// <summary>One region's economic state, as a save has to carry it.</summary>
    public sealed class RegionSnapshot
    {
        public string Name = "";
        public List<Quantity> Prices = new List<Quantity>();
        public List<Quantity> Inventory = new List<Quantity>();
        public List<Quantity> UnmetDemand = new List<Quantity>();
        public List<Quantity> CostRatio = new List<Quantity>();
        public double Cash;
        public double WorkerCash;
        public double WagePremium;
        public double HabitualScale = 1.0;
        public double WorkerDaysEarned;
    }

    /// <summary>The economy as a save has to carry it.</summary>
    public sealed class EconomySnapshot
    {
        public int SchemaVersion = StateCodec.SchemaVersion;
        public int Day;
        public List<Quantity> LaborValues = new List<Quantity>();
        public List<RegionSnapshot> Regions = new List<RegionSnapshot>();
    }

    /// <summary>
    /// Persist the economy so that a reload is the same economy, to the
    /// bit (docs/80).
    ///
    /// **Every double is written as its IEEE 754 bits in hexadecimal, and
    /// never as decimal.** RimWorld runs on Mono, Mono's
    /// <c>double.Parse</c> is not correctly rounded (docs/78 section 3),
    /// and <c>Scribe_Values.Look&lt;double&gt;</c> writes a double as
    /// decimal text and reads it back with a parse. A save that went
    /// through decimal would lose the last bit of some values on every
    /// cycle — rarely, and depending on the value, which is the failure
    /// mode that passes casual testing and breaks a long game later.
    ///
    /// The cost is that a price reads <c>4002661b3af514a2</c> in the save
    /// file rather than <c>2.3</c>. That is accepted: a reader who needs
    /// the number can convert it, and a model that is exact in the
    /// laboratory and not in the save is worse than an unreadable field.
    ///
    /// The whole snapshot encodes to one string, which the game side
    /// hands to a single <c>Scribe_Values.Look</c>. One place knows how a
    /// number is spelled, rather than one per field and a fresh chance to
    /// write a bare double every time someone adds one.
    /// </summary>
    public static class StateCodec
    {
        /// <summary>
        /// Schema 2 is the shell's (profiles, no economy). Economy state
        /// is schema 3: a schema-2 save must load with no economy rather
        /// than read decimal fields as bits, which would not be
        /// wrong-by-a-ulp but catastrophic.
        /// </summary>
        public const int SchemaVersion = 3;

        public static string Encode(double value)
        {
            return BitConverter.DoubleToInt64Bits(value).ToString("x16", CultureInfo.InvariantCulture);
        }

        public static double Decode(string text)
        {
            return BitConverter.Int64BitsToDouble(
                long.Parse(text, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
        }

        public static string Write(EconomySnapshot snapshot)
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("v\t").Append(snapshot.SchemaVersion.ToString(CultureInfo.InvariantCulture)).Append('\n');
            sb.Append("d\t").Append(snapshot.Day.ToString(CultureInfo.InvariantCulture)).Append('\n');
            WritePairs(sb, "lv", snapshot.LaborValues);
            foreach (RegionSnapshot region in snapshot.Regions)
            {
                sb.Append("r\t").Append(Escape(region.Name)).Append('\n');
                WritePairs(sb, "p", region.Prices);
                WritePairs(sb, "i", region.Inventory);
                WritePairs(sb, "u", region.UnmetDemand);
                WritePairs(sb, "c", region.CostRatio);
                WriteScalar(sb, "cash", region.Cash);
                WriteScalar(sb, "wcash", region.WorkerCash);
                WriteScalar(sb, "prem", region.WagePremium);
                WriteScalar(sb, "hab", region.HabitualScale);
                WriteScalar(sb, "wd", region.WorkerDaysEarned);
            }
            return sb.ToString();
        }

        public static EconomySnapshot Read(string text)
        {
            EconomySnapshot snapshot = new EconomySnapshot();
            snapshot.Regions = new List<RegionSnapshot>();
            RegionSnapshot current = null;
            foreach (string rawLine in text.Split('\n'))
            {
                if (rawLine.Length == 0)
                {
                    continue;
                }
                string[] parts = rawLine.Split('\t');
                switch (parts[0])
                {
                    case "v":
                        snapshot.SchemaVersion = int.Parse(parts[1], CultureInfo.InvariantCulture);
                        break;
                    case "d":
                        snapshot.Day = int.Parse(parts[1], CultureInfo.InvariantCulture);
                        break;
                    case "lv":
                        snapshot.LaborValues.Add(new Quantity(Unescape(parts[1]), Decode(parts[2])));
                        break;
                    case "r":
                        current = new RegionSnapshot();
                        current.Name = Unescape(parts[1]);
                        snapshot.Regions.Add(current);
                        break;
                    case "p": current.Prices.Add(new Quantity(Unescape(parts[1]), Decode(parts[2]))); break;
                    case "i": current.Inventory.Add(new Quantity(Unescape(parts[1]), Decode(parts[2]))); break;
                    case "u": current.UnmetDemand.Add(new Quantity(Unescape(parts[1]), Decode(parts[2]))); break;
                    case "c": current.CostRatio.Add(new Quantity(Unescape(parts[1]), Decode(parts[2]))); break;
                    case "cash": current.Cash = Decode(parts[1]); break;
                    case "wcash": current.WorkerCash = Decode(parts[1]); break;
                    case "prem": current.WagePremium = Decode(parts[1]); break;
                    case "hab": current.HabitualScale = Decode(parts[1]); break;
                    case "wd": current.WorkerDaysEarned = Decode(parts[1]); break;
                    default:
                        throw new FormatException("unknown record '" + parts[0] + "'");
                }
            }
            return snapshot;
        }

        private static void WritePairs(StringBuilder sb, string tag, List<Quantity> pairs)
        {
            foreach (Quantity pair in pairs)
            {
                sb.Append(tag).Append('\t').Append(Escape(pair.Name)).Append('\t')
                  .Append(Encode(pair.Amount)).Append('\n');
            }
        }

        private static void WriteScalar(StringBuilder sb, string tag, double value)
        {
            sb.Append(tag).Append('\t').Append(Encode(value)).Append('\n');
        }

        // Names are authored def names and have never contained a tab or a
        // newline; escaping them anyway costs nothing and means a name that
        // one day does cannot silently corrupt the record after it.
        private static string Escape(string name)
        {
            return name.Replace("\\", "\\\\").Replace("\t", "\\t").Replace("\n", "\\n");
        }

        private static string Unescape(string name)
        {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < name.Length; i++)
            {
                if (name[i] == '\\' && i + 1 < name.Length)
                {
                    i++;
                    if (name[i] == 't') sb.Append('\t');
                    else if (name[i] == 'n') sb.Append('\n');
                    else sb.Append(name[i]);
                }
                else
                {
                    sb.Append(name[i]);
                }
            }
            return sb.ToString();
        }
    }
}
