using System;
using System.Collections;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// A string-keyed map that iterates in insertion order, as a Python
    /// <c>dict</c> does (docs/141 §4).
    ///
    /// The laboratory iterates its dicts in insertion order and sums as it
    /// goes, so the order is part of the answer to the last bit. A
    /// <c>Dictionary</c> makes no promise about order, so the port cannot
    /// use one wherever the model iterates. The semantics copied are the
    /// ones the model relies on: assigning an existing key keeps its place;
    /// a new key goes to the end; removing a key closes the gap, and adding
    /// it again puts it at the end.
    /// </summary>
    public sealed class OrderedMap<T> : IEnumerable<KeyValuePair<string, T>>
    {
        private readonly List<string> keys = new List<string>();
        private readonly List<T> values = new List<T>();
        private readonly Dictionary<string, int> index =
            new Dictionary<string, int>(StringComparer.Ordinal);

        public int Count { get { return keys.Count; } }

        public string KeyAt(int position) { return keys[position]; }

        public T ValueAt(int position) { return values[position]; }

        public void SetValueAt(int position, T value) { values[position] = value; }

        public bool ContainsKey(string key) { return index.ContainsKey(key); }

        /// <summary><c>d[key]</c>: throws when absent, as Python's does.</summary>
        public T this[string key]
        {
            get
            {
                int position;
                if (!index.TryGetValue(key, out position))
                {
                    throw new KeyNotFoundException(key);
                }
                return values[position];
            }
            set
            {
                int position;
                if (index.TryGetValue(key, out position))
                {
                    values[position] = value;
                }
                else
                {
                    index[key] = keys.Count;
                    keys.Add(key);
                    values.Add(value);
                }
            }
        }

        public bool TryGetValue(string key, out T value)
        {
            int position;
            if (index.TryGetValue(key, out position))
            {
                value = values[position];
                return true;
            }
            value = default(T);
            return false;
        }

        /// <summary><c>d.get(key, fallback)</c>.</summary>
        public T Get(string key, T fallback)
        {
            int position;
            return index.TryGetValue(key, out position) ? values[position] : fallback;
        }

        /// <summary><c>d.setdefault(key, fallback)</c>.</summary>
        public T SetDefault(string key, T fallback)
        {
            int position;
            if (index.TryGetValue(key, out position))
            {
                return values[position];
            }
            this[key] = fallback;
            return fallback;
        }

        /// <summary><c>d.pop(key)</c> without a default: throws when absent.</summary>
        public T Remove(string key)
        {
            int position;
            if (!index.TryGetValue(key, out position))
            {
                throw new KeyNotFoundException(key);
            }
            T removed = values[position];
            keys.RemoveAt(position);
            values.RemoveAt(position);
            index.Remove(key);
            for (int i = position; i < keys.Count; i++)
            {
                index[keys[i]] = i;
            }
            return removed;
        }

        public void Clear()
        {
            keys.Clear();
            values.Clear();
            index.Clear();
        }

        /// <summary>The keys, in insertion order, as a new list.</summary>
        public List<string> Keys()
        {
            return new List<string>(keys);
        }

        /// <summary>The keys sorted as Python sorts <c>str</c> (ordinal).</summary>
        public List<string> SortedKeys()
        {
            List<string> sorted = new List<string>(keys);
            sorted.Sort(string.CompareOrdinal);
            return sorted;
        }

        public IEnumerator<KeyValuePair<string, T>> GetEnumerator()
        {
            for (int i = 0; i < keys.Count; i++)
            {
                yield return new KeyValuePair<string, T>(keys[i], values[i]);
            }
        }

        IEnumerator IEnumerable.GetEnumerator() { return GetEnumerator(); }
    }
}
