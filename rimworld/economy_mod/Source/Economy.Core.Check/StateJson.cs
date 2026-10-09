using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using SocialProduction.Economy.Core.Model;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// Reads and writes <c>state_codec</c>'s layout (docs/141 §4). Strict by
    /// design: an object missing a field, or carrying one the port does not
    /// know, throws with its path, so the port cannot quietly run on a
    /// state the laboratory did not describe.
    /// </summary>
    public static partial class StateJson
    {
        public const int Schema = 1;

        private static readonly string[] TopFields =
        {
            "schema", "economy", "commodities", "processes", "known_processes",
            "regions", "routes", "shipments", "ledger", "labor_values",
            "regional_labor_values", "stale_labor_values", "throughput",
            "has_daily_extraction", "daily_extraction", "opening_inventory",
        };

        public static EconomyState Read(string text)
        {
            using (JsonDocument document = JsonDocument.Parse(text))
            {
                return Read(document.RootElement);
            }
        }

        public static EconomyState Read(JsonElement e)
        {
            ExpectFields(e, "state", TopFields);
            if (Int(e.GetProperty("schema")) != Schema)
            {
                throw new InvalidDataException("state: schema " + e.GetProperty("schema") + ", expected " + Schema);
            }
            EconomyState x = new EconomyState();
            ReadScalars(e.GetProperty("economy"), x);
            foreach (JsonElement item in e.GetProperty("commodities").EnumerateArray())
            {
                Commodity good = ReadCommodity(item, "commodities", null);
                x.Commodities[good.Name] = good;
            }
            foreach (JsonElement item in e.GetProperty("processes").EnumerateArray())
            {
                Process process = ReadProcess(item, "processes", null);
                x.Processes[process.Name] = process;
            }
            foreach (JsonProperty item in e.GetProperty("known_processes").EnumerateObject())
            {
                x.KnownProcesses[item.Name] = ProcessRef(item.Value, "known_processes." + item.Name, x.Processes);
            }
            foreach (JsonElement item in e.GetProperty("regions").EnumerateArray())
            {
                Region region = ReadRegion(item, "regions", x.Processes);
                x.Regions[region.Name] = region;
            }
            foreach (JsonElement item in e.GetProperty("routes").EnumerateArray())
            {
                x.Routes.Add(ReadRoute(item, "routes", null));
            }
            foreach (JsonElement item in e.GetProperty("shipments").EnumerateArray())
            {
                x.Shipments.Add(ReadShipment(item, "shipments", null));
            }
            x.Ledger = ReadLedger(e.GetProperty("ledger"), "ledger", null);
            x.LaborValues = NumMap(e.GetProperty("labor_values"), "labor_values");
            x.RegionalLaborValues = NestedMap(e.GetProperty("regional_labor_values"), "regional_labor_values");
            foreach (JsonElement item in e.GetProperty("stale_labor_values").EnumerateArray())
            {
                x.StaleLaborValues.Add(Str(item));
            }
            x.Throughput = NestedMap(e.GetProperty("throughput"), "throughput");
            x.HasDailyExtraction = e.GetProperty("has_daily_extraction").GetBoolean();
            ExpectEmpty(e.GetProperty("daily_extraction"), "daily_extraction");
            x.OpeningInventory = NumMap(e.GetProperty("opening_inventory"), "opening_inventory");
            return x;
        }

        public static string Write(EconomyState x)
        {
            using (MemoryStream stream = new MemoryStream())
            {
                using (Utf8JsonWriter w = new Utf8JsonWriter(stream))
                {
                    w.WriteStartObject();
                    w.WriteNumber("schema", Schema);
                    WriteScalars(w, x);
                    w.WriteStartArray("commodities");
                    for (int i = 0; i < x.Commodities.Count; i++) { WriteCommodity(w, x.Commodities.ValueAt(i)); }
                    w.WriteEndArray();
                    w.WriteStartArray("processes");
                    for (int i = 0; i < x.Processes.Count; i++) { WriteProcess(w, x.Processes.ValueAt(i)); }
                    w.WriteEndArray();
                    w.WriteStartObject("known_processes");
                    for (int i = 0; i < x.KnownProcesses.Count; i++)
                    {
                        w.WriteString(x.KnownProcesses.KeyAt(i), x.KnownProcesses.ValueAt(i).Name);
                    }
                    w.WriteEndObject();
                    w.WriteStartArray("regions");
                    for (int i = 0; i < x.Regions.Count; i++) { WriteRegion(w, x.Regions.ValueAt(i)); }
                    w.WriteEndArray();
                    w.WriteStartArray("routes");
                    foreach (Route route in x.Routes) { WriteRoute(w, route); }
                    w.WriteEndArray();
                    w.WriteStartArray("shipments");
                    foreach (Shipment shipment in x.Shipments) { WriteShipment(w, shipment); }
                    w.WriteEndArray();
                    w.WritePropertyName("ledger");
                    WriteLedger(w, x.Ledger);
                    WriteNumMap(w, "labor_values", x.LaborValues);
                    WriteNestedMap(w, "regional_labor_values", x.RegionalLaborValues);
                    w.WriteStartArray("stale_labor_values");
                    foreach (string name in x.StaleLaborValues) { w.WriteStringValue(name); }
                    w.WriteEndArray();
                    WriteNestedMap(w, "throughput", x.Throughput);
                    w.WriteBoolean("has_daily_extraction", x.HasDailyExtraction);
                    w.WriteStartArray("daily_extraction");
                    w.WriteEndArray();
                    WriteNumMap(w, "opening_inventory", x.OpeningInventory);
                    w.WriteEndObject();
                }
                return Encoding.UTF8.GetString(stream.ToArray());
            }
        }

        private static void ExpectFields(JsonElement e, string path, string[] names)
        {
            if (e.ValueKind != JsonValueKind.Object)
            {
                throw new InvalidDataException(path + ": expected an object, found " + e.ValueKind);
            }
            HashSet<string> wanted = new HashSet<string>(names, StringComparer.Ordinal);
            HashSet<string> found = new HashSet<string>(StringComparer.Ordinal);
            foreach (JsonProperty property in e.EnumerateObject())
            {
                if (!wanted.Contains(property.Name))
                {
                    throw new InvalidDataException(path + ": field '" + property.Name + "' is not in the port's model");
                }
                found.Add(property.Name);
            }
            foreach (string name in names)
            {
                if (!found.Contains(name))
                {
                    throw new InvalidDataException(path + ": field '" + name + "' is missing");
                }
            }
        }

        private static void ExpectArray(JsonElement e, string path, int length)
        {
            if (e.ValueKind != JsonValueKind.Array || e.GetArrayLength() != length)
            {
                throw new InvalidDataException(path + ": expected an array of " + length);
            }
        }

        /// <summary>The docked configuration carries none of these (docs/141 §2).</summary>
        private static void ExpectEmpty(JsonElement e, string path)
        {
            bool empty = e.ValueKind == JsonValueKind.Array ? e.GetArrayLength() == 0
                : e.ValueKind == JsonValueKind.Object && !e.EnumerateObject().MoveNext();
            if (!empty)
            {
                throw new InvalidDataException(path + ": not empty, and the docked configuration carries none (docs/141 s2)");
            }
        }

        /// <summary>A float, which Python may have written as an integer.</summary>
        private static double Num(JsonElement e)
        {
            if (e.ValueKind != JsonValueKind.Number)
            {
                throw new InvalidDataException("expected a number, found " + e.ValueKind);
            }
            return e.GetDouble();
        }

        private static int Int(JsonElement e) { return e.GetInt32(); }

        private static string Str(JsonElement e)
        {
            if (e.ValueKind != JsonValueKind.String)
            {
                throw new InvalidDataException("expected a string, found " + e.ValueKind);
            }
            return e.GetString();
        }

        private static OrderedMap<double> NumMap(JsonElement e, string path)
        {
            if (e.ValueKind != JsonValueKind.Object)
            {
                throw new InvalidDataException(path + ": expected an object");
            }
            OrderedMap<double> map = new OrderedMap<double>();
            foreach (JsonProperty property in e.EnumerateObject())
            {
                map[property.Name] = Num(property.Value);
            }
            return map;
        }

        private static OrderedMap<OrderedMap<double>> NestedMap(JsonElement e, string path)
        {
            OrderedMap<OrderedMap<double>> map = new OrderedMap<OrderedMap<double>>();
            foreach (JsonProperty property in e.EnumerateObject())
            {
                map[property.Name] = NumMap(property.Value, path + "." + property.Name);
            }
            return map;
        }

        private static Process ProcessRef(JsonElement e, string path, OrderedMap<Process> processes)
        {
            if (e.ValueKind == JsonValueKind.Null)
            {
                return null;
            }
            Process process;
            if (!processes.TryGetValue(Str(e), out process))
            {
                throw new InvalidDataException(path + ": no process named '" + e.GetString() + "'");
            }
            return process;
        }

        private static void WriteNumMap(Utf8JsonWriter w, string name, OrderedMap<double> map)
        {
            w.WriteStartObject(name);
            for (int i = 0; i < map.Count; i++)
            {
                w.WriteNumber(map.KeyAt(i), map.ValueAt(i));
            }
            w.WriteEndObject();
        }

        private static void WriteNestedMap(Utf8JsonWriter w, string name, OrderedMap<OrderedMap<double>> map)
        {
            w.WriteStartObject(name);
            for (int i = 0; i < map.Count; i++)
            {
                WriteNumMap(w, map.KeyAt(i), map.ValueAt(i));
            }
            w.WriteEndObject();
        }
    }
}
