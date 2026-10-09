using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    /// <summary>
    /// The whole economy, as <c>economy_lab/state_codec.py</c> lays it out
    /// (docs/141 §4). The settings and counters are generated into the
    /// other half of this class; the sections are here.
    /// </summary>
    public sealed partial class EconomyState
    {
        public OrderedMap<Commodity> Commodities = new OrderedMap<Commodity>();
        /// <summary>One per process name. Producers share them by reference,
        /// as the laboratory's producers share one frozen <c>Process</c>.</summary>
        public OrderedMap<Process> Processes = new OrderedMap<Process>();
        /// <summary>The laboratory's <c>known_processes</c>: commodity to process.</summary>
        public OrderedMap<Process> KnownProcesses = new OrderedMap<Process>();
        public OrderedMap<Region> Regions = new OrderedMap<Region>();
        public List<Route> Routes = new List<Route>();
        public List<Shipment> Shipments = new List<Shipment>();
        public Ledger Ledger = new Ledger();
        public OrderedMap<double> LaborValues = new OrderedMap<double>();
        public OrderedMap<OrderedMap<double>> RegionalLaborValues = new OrderedMap<OrderedMap<double>>();
        /// <summary>A set in the laboratory, written by the value solve and
        /// read by nothing in the step; carried sorted.</summary>
        public List<string> StaleLaborValues = new List<string>();
        /// <summary>The laboratory's <c>_throughput</c>: rebuilt each day,
        /// read later in the same day.</summary>
        public OrderedMap<OrderedMap<double>> Throughput = new OrderedMap<OrderedMap<double>>();
        /// <summary>Whether <c>_daily_extraction</c> exists yet: it is created
        /// by the first production phase. Always empty when docked.</summary>
        public bool HasDailyExtraction;
        public OrderedMap<double> OpeningInventory = new OrderedMap<double>();
    }
}
