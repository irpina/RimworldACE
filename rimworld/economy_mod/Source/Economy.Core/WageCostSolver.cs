using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>One producer as the wage-cost refresh sees it.</summary>
    public sealed class WageCostProducer
    {
        public string Name;
        public string Commodity;
        public bool Active = true;
        public ProcessSpec Process;
        /// <summary>Written by the refresh; zero until it runs.</summary>
        public double WageCostPerUnit;
    }

    /// <summary>
    /// The inputs of <c>Economy._update_wage_costs</c> for one region.
    ///
    /// The mass of every commodity is here because the apportionment the
    /// labor share uses is by mass, and a commodity the table does not
    /// name weighs exactly one — the laboratory's
    /// <c>commodities[name].mass_per_unit if name in commodities else 1.0</c>.
    /// </summary>
    public sealed class WageCostProblem
    {
        public string RegionName;
        public bool HasBasket = true;
        /// <summary>Silver per worker-day: <see cref="WageSolver.WageRate"/>.</summary>
        public double WageRate;
        public double TicksPerWorkerDay;
        public List<Quantity> CommodityMass = new List<Quantity>();
        public List<WageCostProducer> Producers = new List<WageCostProducer>();
    }

    /// <summary>
    /// Price each producer's living labor at the current basket cost,
    /// ported from <c>Economy._update_wage_costs</c> (docs/79).
    ///
    /// The daily refresh of one component of effective unit cost, and the
    /// wage's only reach into what a producer's output costs. With no
    /// subsistence basket the rate is zero and every wage cost stays
    /// 0.0, which keeps bare models bit-identical — so the guard is the
    /// laboratory's early return and not a multiply by zero.
    ///
    /// <c>max(ticks_per_worker_day, EPSILON)</c> is the laboratory's, and
    /// is kept even though every scenario has a positive working day:
    /// the port's job is to be the same function, including where it is
    /// defensive.
    /// </summary>
    public static class WageCostSolver
    {
        private const double Epsilon = 1e-9;

        public static void UpdateWageCosts(WageCostProblem problem)
        {
            if (!problem.HasBasket)
            {
                return;
            }
            Dictionary<string, double> mass = new Dictionary<string, double>();
            foreach (Quantity commodity in problem.CommodityMass)
            {
                mass[commodity.Name] = commodity.Amount;
            }
            double wagePerTick =
                problem.WageRate / Math.Max(problem.TicksPerWorkerDay, Epsilon);
            foreach (WageCostProducer producer in problem.Producers)
            {
                if (producer.Active)
                {
                    producer.WageCostPerUnit =
                        LaborPerUnit(producer.Process, producer.Commodity, mass)
                        * wagePerTick;
                }
            }
        }

        /// <summary>
        /// <c>Process.labor_per_unit</c>: the direct labor a unit of this
        /// output bears, after the joint cost is apportioned.  Zero for a
        /// commodity the process does not make, which is the guard that
        /// keeps a by-product's labor off a producer that does not sell it.
        /// </summary>
        public static double LaborPerUnit(
            ProcessSpec process, string commodity, Dictionary<string, double> mass)
        {
            double units = process.OutputOf(commodity);
            if (units <= Epsilon)
            {
                return 0.0;
            }
            return process.DirectLabor
                * LaborValueSolver.ShareOfCost(process, commodity, mass)
                / units;
        }
    }
}
