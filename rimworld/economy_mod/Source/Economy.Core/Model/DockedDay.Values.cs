using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary>
        /// <c>_update_labor_values</c> from the day's realized runs (docs/19),
        /// through the solver ported in docs/53 and checked to the bit since.
        /// This adapter only assembles the solver's problem from the state in
        /// the laboratory's order and writes the answer back in the order the
        /// laboratory's dicts would hold it.
        /// </summary>
        public static void UpdateLaborValues(EconomyState e)
        {
            LaborValueProblem problem = new LaborValueProblem();
            problem.Tolerance = e.LaborValueTolerance;
            problem.MaxIterations = e.LaborValueMaxIterations;
            problem.ServiceLifeDays = e.CapitalServiceLifeDays;
            for (int c = 0; c < e.Commodities.Count; c++)
            {
                Commodity good = e.Commodities.ValueAt(c);
                problem.Commodities.Add(new Quantity(good.Name, good.MassPerUnit));
            }
            Dictionary<Process, ProcessSpec> specs = new Dictionary<Process, ProcessSpec>();
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                problem.Regions.Add(region.Name);
                foreach (Producer producer in region.Producers)
                {
                    if (!producer.Active || producer.LastRuns <= Epsilon)
                    {
                        continue;
                    }
                    ProcessSpec spec;
                    if (!specs.TryGetValue(producer.Process, out spec))
                    {
                        spec = Spec(producer.Process);
                        specs[producer.Process] = spec;
                    }
                    Contributor contributor = new Contributor();
                    contributor.Region = region.Name;
                    contributor.Producer = producer.Name;
                    contributor.Runs = producer.LastRuns;
                    contributor.Process = spec;
                    problem.Contributors.Add(contributor);
                }
            }
            Dictionary<string, double> initial = new Dictionary<string, double>(System.StringComparer.Ordinal);
            for (int i = 0; i < e.LaborValues.Count; i++)
            {
                initial[e.LaborValues.KeyAt(i)] = e.LaborValues.ValueAt(i);
            }
            LaborValueSolution solution = LaborValueSolver.Solve(problem, initial);

            // `values = dict(self.labor_values)`, then `setdefault` for every
            // commodity: the old order, then the newcomers in the economy's.
            OrderedMap<double> values = new OrderedMap<double>();
            for (int i = 0; i < e.LaborValues.Count; i++)
            {
                string name = e.LaborValues.KeyAt(i);
                double solved;
                values[name] = solution.Values.TryGetValue(name, out solved) ? solved : e.LaborValues.ValueAt(i);
            }
            for (int c = 0; c < e.Commodities.Count; c++)
            {
                string name = e.Commodities.KeyAt(c);
                if (!values.ContainsKey(name))
                {
                    double solved;
                    values[name] = solution.Values.TryGetValue(name, out solved) ? solved : 0.0;
                }
            }
            e.LaborValues = values;

            // Regions sorted; within each, what it produced, sorted.
            OrderedMap<OrderedMap<double>> regional = new OrderedMap<OrderedMap<double>>();
            foreach (string regionName in e.Regions.SortedKeys())
            {
                OrderedMap<double> own = new OrderedMap<double>();
                Dictionary<string, double> solved;
                if (solution.RegionalValues.TryGetValue(regionName, out solved))
                {
                    List<string> names = new List<string>(solved.Keys);
                    names.Sort(string.CompareOrdinal);
                    foreach (string name in names)
                    {
                        own[name] = solved[name];
                    }
                }
                regional[regionName] = own;
            }
            e.RegionalLaborValues = regional;

            List<string> stale = new List<string>(solution.Stale);
            stale.Sort(string.CompareOrdinal);
            e.StaleLaborValues = stale;
        }

        private static ProcessSpec Spec(Process process)
        {
            ProcessSpec spec = new ProcessSpec();
            spec.Name = process.Name;
            for (int i = 0; i < process.Outputs.Count; i++)
            {
                spec.Outputs.Add(new Quantity(process.Outputs.KeyAt(i), process.Outputs.ValueAt(i)));
            }
            for (int i = 0; i < process.Inputs.Count; i++)
            {
                spec.Inputs.Add(new Quantity(process.Inputs.KeyAt(i), process.Inputs.ValueAt(i)));
            }
            spec.DirectLabor = process.DirectLabor;
            spec.Apportionment = process.Apportionment;
            spec.CapitalLaborPerCapacity = process.CapitalLaborPerCapacity;
            for (int i = 0; i < process.CapitalBill.Count; i++)
            {
                spec.CapitalBill.Add(new Quantity(process.CapitalBill.KeyAt(i), process.CapitalBill.ValueAt(i)));
            }
            spec.CapitalConstructionLabor = process.CapitalConstructionLabor;
            spec.MachinesPerCapacity = process.MachinesPerCapacity;
            return spec;
        }
    }
}
