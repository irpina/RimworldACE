using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// <c>scale.population</c> (docs/141 slice 2): the real def population,
    /// or an evenly spaced sample of it. The rows themselves are generated
    /// into <c>Population.g.cs</c> as bit patterns.
    /// </summary>
    public static partial class Population
    {
        public sealed class Row
        {
            public readonly string Name;
            public readonly int Depth;
            public readonly double Labor;
            public readonly double Price;

            public Row(string name, int depth, ulong laborBits, ulong priceBits)
            {
                Name = name;
                Depth = depth;
                Labor = BitConverter.Int64BitsToDouble(unchecked((long)laborBits));
                Price = BitConverter.Int64BitsToDouble(unchecked((long)priceBits));
            }
        }

        public static int Count { get { return All.Length; } }

        /// <summary><c>population(limit)</c>: every row, or <paramref name="limit"/>
        /// of them at a fixed stride so the depth mix survives.</summary>
        public static List<Row> Sample(int limit)
        {
            List<Row> rows = new List<Row>(All);
            if (limit >= rows.Count)
            {
                return rows;
            }
            double stride = rows.Count / (double)limit;
            List<Row> sample = new List<Row>(limit);
            for (int index = 0; index < limit; index++)
            {
                sample.Add(rows[(int)(index * stride)]);
            }
            return sample;
        }
    }

    /// <summary>
    /// <c>scale._Random</c>: SplitMix64, and Python's correctly rounded
    /// conversion of its draws to a double.
    /// </summary>
    public sealed class LabRandom
    {
        private ulong state;

        public LabRandom(long seed)
        {
            state = unchecked((ulong)seed);
        }

        public ulong Next()
        {
            unchecked
            {
                state += 0x9E3779B97F4A7C15UL;
                ulong z = state;
                z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
                return z ^ (z >> 31);
            }
        }

        public int Below(int limit)
        {
            return (int)(Next() % (ulong)Math.Max(limit, 1));
        }

        /// <summary>Python's <c>float(int)</c> for a 64-bit value: round to
        /// nearest, ties to even. Done by hand because a runtime's own
        /// <c>ulong</c> conversion is not promised to round once.</summary>
        public static double ToDouble(ulong value)
        {
            if (value < (1UL << 53))
            {
                return (long)value;
            }
            int length = 64;
            while ((value & (1UL << (length - 1))) == 0)
            {
                length--;
            }
            int shift = length - 53;
            ulong kept = value >> shift;
            ulong rest = value & ((1UL << shift) - 1);
            ulong half = 1UL << (shift - 1);
            if (rest > half || (rest == half && (kept & 1UL) == 1UL))
            {
                kept++;
            }
            double scale = BitConverter.Int64BitsToDouble((long)(1023 + shift) << 52);
            return (long)kept * scale;
        }
    }
}
