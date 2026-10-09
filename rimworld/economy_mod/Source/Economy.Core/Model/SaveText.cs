using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// The save format of docs/143 §2: the whole docked state as one string
    /// the game's runtime can write and read with no dependency.
    ///
    /// Tokens separated by single spaces. A double is its IEEE-754 bits as
    /// sixteen hex digits, never decimal, for the reason <c>StateCodec</c>
    /// gives: Mono's <c>double.Parse</c> is not correctly rounded. An
    /// integer is decimal; a boolean is 0 or 1; a string is <c>s</c>
    /// followed by its characters, with anything outside printable ASCII,
    /// and the escape character itself, written as <c>%</c> and four hex
    /// digits. Every collection is preceded by its count, so the reader
    /// never guesses where one ends.
    ///
    /// The fields and their order are the JSON codec's (<c>state_codec</c>),
    /// generated into <c>SaveText.g.cs</c>; this half lays out the sections.
    /// </summary>
    public static partial class SaveText
    {
        public const string Magic = "docked-economy";
        public const int Schema = 4;

        public static string Write(EconomyState x)
        {
            TokenWriter w = new TokenWriter();
            w.Raw(Magic);
            w.Integer(Schema);
            WriteScalars(w, x);
            w.Integer(x.Commodities.Count);
            for (int i = 0; i < x.Commodities.Count; i++) { WriteCommodity(w, x.Commodities.ValueAt(i)); }
            w.Integer(x.Processes.Count);
            for (int i = 0; i < x.Processes.Count; i++) { WriteProcess(w, x.Processes.ValueAt(i)); }
            w.Integer(x.KnownProcesses.Count);
            for (int i = 0; i < x.KnownProcesses.Count; i++)
            {
                w.Text(x.KnownProcesses.KeyAt(i));
                w.Text(x.KnownProcesses.ValueAt(i).Name);
            }
            w.Integer(x.Regions.Count);
            for (int i = 0; i < x.Regions.Count; i++) { WriteRegion(w, x.Regions.ValueAt(i)); }
            w.Integer(x.Routes.Count);
            foreach (Route route in x.Routes) { WriteRoute(w, route); }
            w.Integer(x.Shipments.Count);
            foreach (Shipment shipment in x.Shipments) { WriteShipment(w, shipment); }
            WriteLedger(w, x.Ledger);
            WriteNumMap(w, x.LaborValues);
            WriteNestedMap(w, x.RegionalLaborValues);
            w.Integer(x.StaleLaborValues.Count);
            foreach (string name in x.StaleLaborValues) { w.Text(name); }
            WriteNestedMap(w, x.Throughput);
            w.Boolean(x.HasDailyExtraction);
            WriteNumMap(w, x.OpeningInventory);
            w.Raw("end");
            return w.ToString();
        }

        public static EconomyState Read(string text)
        {
            TokenReader r = new TokenReader(text);
            r.Expect(Magic);
            int schema = r.Integer();
            if (schema != Schema)
            {
                throw new InvalidDataException("save: schema " + schema + ", expected " + Schema);
            }
            EconomyState x = new EconomyState();
            ReadScalars(r, x);
            for (int i = r.Count(); i > 0; i--)
            {
                Commodity good = ReadCommodity(r, null);
                x.Commodities[good.Name] = good;
            }
            for (int i = r.Count(); i > 0; i--)
            {
                Process process = ReadProcess(r, null);
                x.Processes[process.Name] = process;
            }
            for (int i = r.Count(); i > 0; i--)
            {
                string commodity = r.Text();
                x.KnownProcesses[commodity] = Resolve(r.Text(), x.Processes);
            }
            for (int i = r.Count(); i > 0; i--)
            {
                Region region = ReadRegion(r, x.Processes);
                x.Regions[region.Name] = region;
            }
            for (int i = r.Count(); i > 0; i--) { x.Routes.Add(ReadRoute(r, null)); }
            for (int i = r.Count(); i > 0; i--) { x.Shipments.Add(ReadShipment(r, null)); }
            x.Ledger = ReadLedger(r, null);
            x.LaborValues = ReadNumMap(r);
            x.RegionalLaborValues = ReadNestedMap(r);
            for (int i = r.Count(); i > 0; i--) { x.StaleLaborValues.Add(r.Text()); }
            x.Throughput = ReadNestedMap(r);
            x.HasDailyExtraction = r.Boolean();
            x.OpeningInventory = ReadNumMap(r);
            r.Expect("end");
            r.ExpectFinished();
            return x;
        }

        private static void WriteNumMap(TokenWriter w, OrderedMap<double> map)
        {
            w.Integer(map.Count);
            for (int i = 0; i < map.Count; i++)
            {
                w.Text(map.KeyAt(i));
                w.Number(map.ValueAt(i));
            }
        }

        private static OrderedMap<double> ReadNumMap(TokenReader r)
        {
            OrderedMap<double> map = new OrderedMap<double>();
            for (int i = r.Count(); i > 0; i--)
            {
                string key = r.Text();
                if (map.ContainsKey(key))
                {
                    throw new InvalidDataException("save: key '" + key + "' twice in one map");
                }
                map[key] = r.Number();
            }
            return map;
        }

        private static void WriteNestedMap(TokenWriter w, OrderedMap<OrderedMap<double>> map)
        {
            w.Integer(map.Count);
            for (int i = 0; i < map.Count; i++)
            {
                w.Text(map.KeyAt(i));
                WriteNumMap(w, map.ValueAt(i));
            }
        }

        private static OrderedMap<OrderedMap<double>> ReadNestedMap(TokenReader r)
        {
            OrderedMap<OrderedMap<double>> map = new OrderedMap<OrderedMap<double>>();
            for (int i = r.Count(); i > 0; i--)
            {
                string key = r.Text();
                map[key] = ReadNumMap(r);
            }
            return map;
        }

        private static void WriteProcessRef(TokenWriter w, Process process)
        {
            if (process == null)
            {
                w.Raw("-");
            }
            else
            {
                w.Text(process.Name);
            }
        }

        private static Process ReadProcessRef(TokenReader r, OrderedMap<Process> processes)
        {
            if (r.TryExpect("-"))
            {
                return null;
            }
            return Resolve(r.Text(), processes);
        }

        private static Process Resolve(string name, OrderedMap<Process> processes)
        {
            Process process;
            if (processes == null || !processes.TryGetValue(name, out process))
            {
                throw new InvalidDataException("save: no process named '" + name + "'");
            }
            return process;
        }
    }

    /// <summary>Writes the tokens of <see cref="SaveText"/>.</summary>
    public sealed class TokenWriter
    {
        private readonly StringBuilder text = new StringBuilder();

        public void Raw(string token)
        {
            if (text.Length > 0)
            {
                text.Append(' ');
            }
            text.Append(token);
        }

        public void Number(double value)
        {
            Raw(BitConverter.DoubleToInt64Bits(value).ToString("X16", CultureInfo.InvariantCulture));
        }

        public void Integer(int value)
        {
            Raw(value.ToString(CultureInfo.InvariantCulture));
        }

        public void Boolean(bool value)
        {
            Raw(value ? "1" : "0");
        }

        public void Text(string value)
        {
            if (value == null)
            {
                throw new ArgumentNullException("value", "the save format has no null string");
            }
            StringBuilder token = new StringBuilder(value.Length + 1);
            token.Append('s');
            foreach (char c in value)
            {
                if (c > ' ' && c < (char)127 && c != '%')
                {
                    token.Append(c);
                }
                else
                {
                    token.Append('%').Append(((int)c).ToString("X4", CultureInfo.InvariantCulture));
                }
            }
            Raw(token.ToString());
        }

        public override string ToString()
        {
            return text.ToString();
        }
    }

    /// <summary>Reads the tokens of <see cref="SaveText"/>, strictly.</summary>
    public sealed class TokenReader
    {
        private readonly string text;
        private int position;

        public TokenReader(string text)
        {
            this.text = text ?? "";
        }

        private string Next()
        {
            if (position >= text.Length)
            {
                throw new InvalidDataException("save: ended early at character " + position);
            }
            int end = text.IndexOf(' ', position);
            if (end < 0)
            {
                end = text.Length;
            }
            string token = text.Substring(position, end - position);
            position = end + 1;
            if (token.Length == 0)
            {
                throw new InvalidDataException("save: empty token at character " + (end));
            }
            return token;
        }

        private string Peek()
        {
            int saved = position;
            string token = Next();
            position = saved;
            return token;
        }

        public void Expect(string token)
        {
            string found = Next();
            if (found != token)
            {
                throw new InvalidDataException("save: expected '" + token + "', found '" + found + "'");
            }
        }

        public bool TryExpect(string token)
        {
            if (position < text.Length && Peek() == token)
            {
                Next();
                return true;
            }
            return false;
        }

        public void ExpectFinished()
        {
            if (position < text.Length)
            {
                throw new InvalidDataException("save: text after the end, at character " + position);
            }
        }

        public double Number()
        {
            string token = Next();
            long bits;
            if (token.Length != 16 || !long.TryParse(token, NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture, out bits))
            {
                throw new InvalidDataException("save: '" + token + "' is not a double's sixteen hex digits");
            }
            return BitConverter.Int64BitsToDouble(bits);
        }

        public int Integer()
        {
            string token = Next();
            int value;
            if (!int.TryParse(token, NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out value))
            {
                throw new InvalidDataException("save: '" + token + "' is not an integer");
            }
            return value;
        }

        public int Count()
        {
            int count = Integer();
            if (count < 0)
            {
                throw new InvalidDataException("save: negative count " + count);
            }
            return count;
        }

        public bool Boolean()
        {
            string token = Next();
            if (token == "1") { return true; }
            if (token == "0") { return false; }
            throw new InvalidDataException("save: '" + token + "' is not 0 or 1");
        }

        public string Text()
        {
            string token = Next();
            if (token[0] != 's')
            {
                throw new InvalidDataException("save: '" + token + "' is not a string");
            }
            StringBuilder value = new StringBuilder(token.Length);
            for (int i = 1; i < token.Length; i++)
            {
                char c = token[i];
                if (c != '%')
                {
                    value.Append(c);
                    continue;
                }
                int code;
                if (token.Length - i - 1 < 4
                    || !int.TryParse(token.Substring(i + 1, 4), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture, out code))
                {
                    throw new InvalidDataException("save: bad escape in '" + token + "'");
                }
                value.Append((char)code);
                i += 4;
            }
            return value.ToString();
        }
    }
}
