using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// One day of the docked economy (docs/138), transliterated phase by
    /// phase from <c>Economy.step</c> in <c>economy_lab/model.py</c>
    /// (docs/141 §4). Each phase is checked against the laboratory's state
    /// before and after it, to the bit.
    ///
    /// Only the branches the docked configuration takes are carried.
    /// <see cref="Refuse"/> throws for any other configuration, naming the
    /// switch, so this cannot quietly run a model nobody docked.
    /// </summary>
    public static partial class DockedDay
    {
        /// <summary>The model's <c>EPSILON</c>.</summary>
        public const double Epsilon = 1e-9;

        /// <summary>A phase: its laboratory name and the code.</summary>
        public struct Phase
        {
            public readonly string Name;
            public readonly Action<EconomyState> Run;

            public Phase(string name, Action<EconomyState> run)
            {
                Name = name;
                Run = run;
            }
        }

        /// <summary>
        /// The ported phases by the laboratory's method name. A phase absent
        /// from here has not been ported yet.
        /// </summary>
        public static readonly Dictionary<string, Action<EconomyState>> Ported =
            new Dictionary<string, Action<EconomyState>>(StringComparer.Ordinal)
            {
                { "begin", Begin },
                { "_migrate", Migrate },
                { "_arrive_shipments", ArriveShipments },
                { "_complete_projects", CompleteProjects },
                { "_track_differential_rent", TrackDifferentialRent },
                { "_refresh_throughput", RefreshThroughput },
                { "_consume", Consume },
                { "_workers_consume", WorkersConsume },
                { "_update_prices", UpdatePrices },
                { "_settle_purses", SettlePurses },
                { "_update_expectations", UpdateExpectations },
            };

        /// <summary>
        /// docs/141 §2: the switches the docked configuration sets, and only
        /// those. Called before every day.
        /// </summary>
        public static void Refuse(EconomyState e)
        {
            Require(e.ProducerCash, "producer_cash must be on");
            Require(e.PostedPrices, "posted_prices must be on");
            Require(e.Accumulate, "accumulate (rule two) must be on");
            Require(e.FundSpendingRate > 0.0, "fund_spending_rate (rule one) must be positive");
            Require(!e.Procurement, "procurement is not carried");
            Require(!e.EntryOnMargin, "entry_on_margin is not carried");
            Require(!e.ExitOnReturn, "exit_on_return is not carried");
            Require(!e.CapacityExit, "capacity_exit is not carried");
            Require(!e.SalesFollowProduction, "sales_follow_production is not carried");
            Require(e.WorkerMobilityStrength == 0.0, "worker mobility is not carried");
            Require(e.WageBargainingStrength == 0.0, "wage bargaining is not carried");
            Require(e.HabituationSpeed == 0.0, "habituation is not carried");
            Require(e.InputRationing == "proportional", "only proportional rationing is carried");
            Require((e.Day + 1) % e.InvestmentIntervalDays != 0, "investment is not carried, and tomorrow is an investment day");
        }

        private static void Require(bool condition, string what)
        {
            if (!condition)
            {
                throw new NotSupportedException("not the docked configuration (docs/141 s2): " + what);
            }
        }

        /// <summary><c>Ledger.add</c>.</summary>
        internal static void Add(OrderedMap<double> bucket, string commodity, double amount)
        {
            bucket[commodity] = bucket.Get(commodity, 0.0) + amount;
        }

        /// <summary><c>step</c>'s <c>self.day += 1</c>.</summary>
        public static void Begin(EconomyState e)
        {
            Refuse(e);
            e.Day += 1;
        }

        /// <summary><c>_migrate</c>: zero strength returns before touching anything.</summary>
        public static void Migrate(EconomyState e)
        {
            Require(e.WorkerMobilityStrength == 0.0, "worker mobility is not carried");
        }

        /// <summary><c>_arrive_shipments</c>, the branch without procurement.</summary>
        public static void ArriveShipments(EconomyState e)
        {
            List<Shipment> pending = new List<Shipment>();
            foreach (Shipment shipment in e.Shipments)
            {
                if (shipment.ArrivalDay > e.Day)
                {
                    pending.Add(shipment);
                    continue;
                }
                Region destination = e.Regions[shipment.Destination];
                destination.Inventory[shipment.Commodity] = destination.Inventory[shipment.Commodity] + shipment.Quantity;
                destination.ImportedTotal[shipment.Commodity] = destination.ImportedTotal[shipment.Commodity] + shipment.Quantity;
            }
            e.Shipments = pending;
        }

        /// <summary><c>_complete_projects</c>: the docked economy has none,
        /// which the state reader already enforces.</summary>
        public static void CompleteProjects(EconomyState e)
        {
        }

        /// <summary><c>_track_differential_rent</c>: no region holds a reserve
        /// when docked (enforced on read), so there is nothing to compare.</summary>
        public static void TrackDifferentialRent(EconomyState e)
        {
        }

        /// <summary><c>_update_expectations</c>.</summary>
        public static void UpdateExpectations(EconomyState e)
        {
            double alpha = e.ExpectationAlpha;
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                for (int c = 0; c < e.Commodities.Count; c++)
                {
                    string name = e.Commodities.KeyAt(c);
                    region.ExpectedPrices[name] =
                        (1.0 - alpha) * region.ExpectedPrices[name]
                        + alpha * region.Prices[name];
                }
            }
        }
    }
}
