using System;
using System.Collections.Generic;
using System.Text.Json;

namespace SocialProduction.Economy.Check
{
    /// <summary>
    /// Two states compared field by field, in order, numbers by their bits
    /// (docs/141 §4). Order is compared because a map's insertion order is
    /// part of the model: it decides the order of every later sum.
    /// </summary>
    public static class StateCompare
    {
        /// <summary>The first <paramref name="limit"/> differences, each with its path.</summary>
        public static List<string> Differences(string expected, string observed, int limit)
        {
            List<string> found = new List<string>();
            using (JsonDocument a = JsonDocument.Parse(expected))
            using (JsonDocument b = JsonDocument.Parse(observed))
            {
                Walk(a.RootElement, b.RootElement, "state", found, limit);
            }
            return found;
        }

        private static void Walk(JsonElement a, JsonElement b, string path, List<string> found, int limit)
        {
            if (found.Count >= limit)
            {
                return;
            }
            if (a.ValueKind == JsonValueKind.Number && b.ValueKind == JsonValueKind.Number)
            {
                double x = a.GetDouble();
                double y = b.GetDouble();
                if (BitConverter.DoubleToInt64Bits(x) != BitConverter.DoubleToInt64Bits(y))
                {
                    found.Add(path + ": expected " + x.ToString("R") + ", observed " + y.ToString("R")
                        + " (" + Ulps(x, y) + " ulp)");
                }
                return;
            }
            if (a.ValueKind != b.ValueKind)
            {
                found.Add(path + ": expected " + a.ValueKind + ", observed " + b.ValueKind);
                return;
            }
            switch (a.ValueKind)
            {
                case JsonValueKind.Object:
                    {
                        List<JsonProperty> left = new List<JsonProperty>(a.EnumerateObject());
                        List<JsonProperty> right = new List<JsonProperty>(b.EnumerateObject());
                        if (left.Count != right.Count)
                        {
                            found.Add(path + ": expected " + left.Count + " entries, observed " + right.Count);
                        }
                        int n = Math.Min(left.Count, right.Count);
                        for (int i = 0; i < n; i++)
                        {
                            if (left[i].Name != right[i].Name)
                            {
                                found.Add(path + ": entry " + i + " expected key '" + left[i].Name + "', observed '" + right[i].Name + "'");
                                return;
                            }
                            Walk(left[i].Value, right[i].Value, path + "." + left[i].Name, found, limit);
                        }
                        return;
                    }
                case JsonValueKind.Array:
                    {
                        int n = Math.Min(a.GetArrayLength(), b.GetArrayLength());
                        if (a.GetArrayLength() != b.GetArrayLength())
                        {
                            found.Add(path + ": expected length " + a.GetArrayLength() + ", observed " + b.GetArrayLength());
                        }
                        for (int i = 0; i < n; i++)
                        {
                            Walk(a[i], b[i], path + "[" + i + "]", found, limit);
                        }
                        return;
                    }
                case JsonValueKind.String:
                    if (a.GetString() != b.GetString())
                    {
                        found.Add(path + ": expected '" + a.GetString() + "', observed '" + b.GetString() + "'");
                    }
                    return;
                default:
                    return;
            }
        }

        public static long Ulps(double x, double y)
        {
            long a = BitConverter.DoubleToInt64Bits(x);
            long b = BitConverter.DoubleToInt64Bits(y);
            if (a < 0) { a = long.MinValue - a; }
            if (b < 0) { b = long.MinValue - b; }
            return Math.Abs(a - b);
        }
    }
}
