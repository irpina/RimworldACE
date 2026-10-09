using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary><c>_dispatch_arbitrage</c>, without procurement: routes in
        /// name order, the widest spread first on each.</summary>
        public static void DispatchArbitrage(EconomyState e)
        {
            List<Route> routes = new List<Route>(e.Routes);
            // Python's sort is stable; ties keep list order.
            List<int> order = new List<int>();
            for (int i = 0; i < routes.Count; i++)
            {
                order.Add(i);
            }
            order.Sort(delegate (int x, int y)
            {
                int byA = string.CompareOrdinal(routes[x].A, routes[y].A);
                if (byA != 0) { return byA; }
                int byB = string.CompareOrdinal(routes[x].B, routes[y].B);
                return byB != 0 ? byB : x.CompareTo(y);
            });
            List<string> names = e.Commodities.SortedKeys();
            foreach (int index in order)
            {
                Route route = routes[index];
                double remainingCapacity = route.CapacityPerDay;
                Region a = e.Regions[route.A];
                Region b = e.Regions[route.B];
                double freight = route.FreightPerUnit * (1.0 + route.RiskMarkup);

                List<KeyValuePair<double, string>> candidates = new List<KeyValuePair<double, string>>();
                foreach (string name in names)
                {
                    double spread = Math.Abs(a.Prices[name] - b.Prices[name]) - freight;
                    if (spread > 0)
                    {
                        candidates.Add(new KeyValuePair<double, string>(spread, name));
                    }
                }
                // Widest first, then by name: names are unique, so the order is total.
                candidates.Sort(delegate (KeyValuePair<double, string> x, KeyValuePair<double, string> y)
                {
                    double nx = -x.Key;
                    double ny = -y.Key;
                    if (nx < ny) { return -1; }
                    if (nx > ny) { return 1; }
                    return string.CompareOrdinal(x.Value, y.Value);
                });

                foreach (KeyValuePair<double, string> candidate in candidates)
                {
                    string name = candidate.Value;
                    if (remainingCapacity <= Epsilon)
                    {
                        break;
                    }
                    Region source;
                    Region destination;
                    if (b.Prices[name] > a.Prices[name] + freight)
                    {
                        source = a;
                        destination = b;
                    }
                    else if (a.Prices[name] > b.Prices[name] + freight)
                    {
                        source = b;
                        destination = a;
                    }
                    else
                    {
                        continue;
                    }

                    Commodity commodity = e.Commodities[name];
                    double sourceTarget = e.Throughput[source.Name][name] * commodity.TargetInventoryDays;
                    double destinationTarget = e.Throughput[destination.Name][name] * commodity.TargetInventoryDays;
                    double exportable = Lab.Max(0.0, source.Inventory[name] - sourceTarget);
                    double shortage = Lab.Max(0.0, destinationTarget - destination.Inventory[name]);
                    double grossSpread = destination.Prices[name] - source.Prices[name] - freight;
                    double speculativeRoom = destinationTarget * Lab.Min(
                        e.SpeculativeInventoryLimit,
                        grossSpread / Lab.Max(destination.Prices[name], Epsilon));
                    double importRoom = shortage + Lab.Max(0.0, speculativeRoom);
                    double quantity = Lab.Min(Lab.Min(exportable, importRoom), remainingCapacity);
                    if (quantity <= Epsilon)
                    {
                        continue;
                    }

                    double unitPayment = source.Prices[name] + freight;
                    double affordable = destination.Cash / Lab.Max(unitPayment, Epsilon);
                    quantity = Lab.Min(quantity, affordable);
                    if (quantity <= Epsilon)
                    {
                        continue;
                    }

                    source.Inventory[name] = source.Inventory[name] - quantity;
                    source.ExportedTotal[name] = source.ExportedTotal[name] + quantity;
                    double payment = source.Prices[name] * quantity;
                    double freightPayment = freight * quantity;
                    payment = PaySellers(e, source, name, payment, SupplyShares(e, source), false, quantity);
                    destination.Cash -= payment + freightPayment;
                    e.Ledger.TransportCash += freightPayment;
                    Shipment shipment = new Shipment();
                    shipment.Commodity = name;
                    shipment.Quantity = quantity;
                    shipment.Source = source.Name;
                    shipment.Destination = destination.Name;
                    shipment.DispatchDay = e.Day;
                    shipment.ArrivalDay = e.Day + route.TravelDays;
                    shipment.SourceUnitPrice = source.Prices[name];
                    shipment.FreightPerUnit = freight;
                    e.Shipments.Add(shipment);
                    remainingCapacity -= quantity;
                }
            }
        }
    }
}
