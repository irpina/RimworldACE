using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// Labor values solved from the process graph (docs/19), ported to the
    /// bit from <c>Economy._update_labor_values</c> (docs/53).
    ///
    /// Value in work-ticks is transferred value -- inputs at their own
    /// social values, plus the plant worn out -- plus living labor, per unit
    /// of output, aggregated over every active producer in every region:
    /// total labor over total output.  A fixed point in the values, iterated
    /// rather than inverted, because iteration converges exactly when the
    /// matrix is productive and survives a cyclic graph.
    ///
    /// Every accumulation here is in the order the laboratory does it and
    /// with the summation the laboratory uses, because the answer is a
    /// floating-point number and the order is part of it.
    /// </summary>
    public static class LaborValueSolver
    {
        private const double Epsilon = 1e-9;

        public static LaborValueSolution Solve(
            LaborValueProblem problem, IReadOnlyDictionary<string, double> initial)
        {
            Dictionary<string, double> mass = new Dictionary<string, double>();
            List<string> commodityNames = new List<string>();
            foreach (Quantity commodity in problem.Commodities)
            {
                mass[commodity.Name] = commodity.Amount;
                commodityNames.Add(commodity.Name);
            }

            List<Contributor> contributors = new List<Contributor>();
            foreach (Contributor contributor in problem.Contributors)
            {
                if (contributor.Runs > Epsilon)
                {
                    contributors.Add(contributor);
                }
            }

            // Total output per commodity fixes which values this solve can
            // determine; the rest keep the value they had.  Plain `+=`, in
            // contributor order, over the outputs in insertion order --
            // exactly as the laboratory accumulates it.
            Dictionary<string, double> output = new Dictionary<string, double>();
            foreach (Contributor contributor in contributors)
            {
                foreach (Quantity produced in contributor.Process.Outputs)
                {
                    if (!mass.ContainsKey(produced.Name))
                    {
                        continue;
                    }
                    double previous;
                    output.TryGetValue(produced.Name, out previous);
                    output[produced.Name] = previous + contributor.Runs * produced.Amount;
                }
            }
            List<string> solvable = new List<string>();
            foreach (KeyValuePair<string, double> entry in output)
            {
                if (entry.Value > Epsilon)
                {
                    solvable.Add(entry.Key);
                }
            }
            solvable.Sort(string.CompareOrdinal);

            LaborValueSolution solution = new LaborValueSolution();
            HashSet<string> solvableSet = new HashSet<string>(solvable);
            foreach (string name in commodityNames)
            {
                if (!solvableSet.Contains(name))
                {
                    solution.Stale.Add(name);
                }
            }
            solution.Stale.Sort(string.CompareOrdinal);

            Dictionary<string, double> values = new Dictionary<string, double>();
            foreach (KeyValuePair<string, double> entry in initial)
            {
                values[entry.Key] = entry.Value;
            }
            foreach (string name in commodityNames)
            {
                if (!values.ContainsKey(name))
                {
                    values[name] = 0.0;
                }
            }

            bool converged = false;
            int iterations = 0;
            for (int iteration = 0; iteration < problem.MaxIterations; iteration++)
            {
                iterations = iteration + 1;
                Dictionary<string, double> labor = new Dictionary<string, double>();
                foreach (string name in solvable)
                {
                    labor[name] = 0.0;
                }
                foreach (Contributor contributor in contributors)
                {
                    double runs = contributor.Runs;
                    ProcessSpec process = contributor.Process;
                    double perRunTotal = process.DirectLabor + CarriedLabor(process, values);
                    double laborPerCapacity = CapitalLaborPerCapacity(process, values);
                    foreach (string name in SortedOutputNames(process))
                    {
                        if (!labor.ContainsKey(name))
                        {
                            continue;
                        }
                        double share = ShareOfCost(process, name, mass);
                        double contributed = runs * perRunTotal * share;
                        double capitalLabor = CapitalConsumedPerUnit(
                            process, name, problem.ServiceLifeDays, mass, laborPerCapacity);
                        contributed += runs * process.OutputOf(name) * capitalLabor;
                        labor[name] += contributed;
                    }
                }
                Dictionary<string, double> revised = new Dictionary<string, double>(values);
                foreach (string name in solvable)
                {
                    revised[name] = labor[name] / output[name];
                }
                bool settled = true;
                foreach (string name in solvable)
                {
                    if (!(Math.Abs(revised[name] - values[name]) <= problem.Tolerance))
                    {
                        settled = false;
                        break;
                    }
                }
                values = revised;
                if (settled)
                {
                    converged = true;
                    break;
                }
            }
            if (!converged)
            {
                throw new NotProductiveException(
                    "labor value solve did not converge; the input matrix is not "
                    + "productive (some commodity consumes more of itself, directly "
                    + "or indirectly, than it produces)");
            }

            solution.Iterations = iterations;
            solution.Values = values;

            // Individual values: a region's own living labor plus its inputs
            // at prevailing *social* values.  One pass, regions sorted.
            List<string> regionNames = new List<string>(problem.Regions);
            regionNames.Sort(string.CompareOrdinal);
            foreach (string regionName in regionNames)
            {
                Dictionary<string, double> regionLabor = new Dictionary<string, double>();
                Dictionary<string, double> regionOutput = new Dictionary<string, double>();
                foreach (Contributor contributor in problem.Contributors)
                {
                    if (contributor.Region != regionName || contributor.Runs <= Epsilon)
                    {
                        continue;
                    }
                    double runs = contributor.Runs;
                    ProcessSpec process = contributor.Process;
                    double perRunTotal = process.DirectLabor + CarriedLabor(process, values);
                    double laborPerCapacity = CapitalLaborPerCapacity(process, values);
                    foreach (Quantity produced in SortedOutputs(process))
                    {
                        if (!mass.ContainsKey(produced.Name))
                        {
                            continue;
                        }
                        double capitalLabor = CapitalConsumedPerUnit(
                            process, produced.Name, problem.ServiceLifeDays, mass, laborPerCapacity);
                        double previousLabor;
                        regionLabor.TryGetValue(produced.Name, out previousLabor);
                        regionLabor[produced.Name] =
                            previousLabor
                            + runs * perRunTotal * ShareOfCost(process, produced.Name, mass)
                            + runs * produced.Amount * capitalLabor;
                        double previousOutput;
                        regionOutput.TryGetValue(produced.Name, out previousOutput);
                        regionOutput[produced.Name] = previousOutput + runs * produced.Amount;
                    }
                }
                Dictionary<string, double> individual = new Dictionary<string, double>();
                List<string> produced_names = new List<string>(regionOutput.Keys);
                produced_names.Sort(string.CompareOrdinal);
                foreach (string name in produced_names)
                {
                    double total = regionOutput[name];
                    if (total > Epsilon)
                    {
                        individual[name] = regionLabor[name] / total;
                    }
                }
                solution.RegionalValues[regionName] = individual;
            }
            return solution;
        }

        /// <summary>Inputs at the given values, per run: a <c>sum()</c> over sorted names.</summary>
        private static double CarriedLabor(ProcessSpec process, Dictionary<string, double> values)
        {
            if (process.Inputs.Count == 0)
            {
                return 0.0;
            }
            List<Quantity> inputs = new List<Quantity>(process.Inputs);
            inputs.Sort(CompareByName);
            List<double> terms = new List<double>(inputs.Count);
            foreach (Quantity input in inputs)
            {
                double value;
                values.TryGetValue(input.Name, out value);
                terms.Add(input.Amount * value);
            }
            return CompensatedSum.Of(terms);
        }

        /// <summary>
        /// Embodied labor of the plant behind one unit of daily capacity:
        /// authored where the process carries no bill, else the bill at the
        /// current iterate plus the construction labor, times the machines.
        /// </summary>
        private static double CapitalLaborPerCapacity(ProcessSpec process, Dictionary<string, double> values)
        {
            if (process.CapitalBill.Count == 0)
            {
                return process.CapitalLaborPerCapacity;
            }
            List<Quantity> bill = new List<Quantity>(process.CapitalBill);
            bill.Sort(CompareByName);
            List<double> terms = new List<double>(bill.Count);
            foreach (Quantity item in bill)
            {
                double value;
                values.TryGetValue(item.Name, out value);
                terms.Add(item.Amount * value);
            }
            return process.MachinesPerCapacity
                * (CompensatedSum.Of(terms) + process.CapitalConstructionLabor);
        }

        /// <summary>Fixed capital transferred to one unit of output, in ticks.</summary>
        private static double CapitalConsumedPerUnit(
            ProcessSpec process,
            string commodity,
            double serviceLifeDays,
            Dictionary<string, double> mass,
            double laborPerCapacity)
        {
            if (serviceLifeDays <= Epsilon)
            {
                return 0.0;
            }
            double share = ShareOfCost(process, commodity, mass);
            double units = process.OutputOf(commodity);
            if (units <= Epsilon)
            {
                return 0.0;
            }
            return laborPerCapacity * share / serviceLifeDays;
        }

        /// <summary>
        /// Fraction of a process's joint cost borne by one output: one for a
        /// single output, else by mass, with the mass total a <c>sum()</c>
        /// over the outputs in insertion order.
        /// </summary>
        /// <summary>
        /// Exposed for <see cref="WageCostSolver"/>, which needs the same
        /// apportionment the value solve uses (docs/79).  One
        /// implementation rather than two: a second copy of this would be
        /// a second thing to keep in step with the laboratory.
        /// </summary>
        internal static double ShareOfCost(ProcessSpec process, string commodity, Dictionary<string, double> mass)
        {
            double amount = process.OutputOf(commodity);
            bool present = false;
            foreach (Quantity produced in process.Outputs)
            {
                if (produced.Name == commodity)
                {
                    present = true;
                    break;
                }
            }
            if (!present)
            {
                return 0.0;
            }
            if (process.Outputs.Count == 1)
            {
                return 1.0;
            }
            if (process.Apportionment != "mass")
            {
                throw new ArgumentException("unknown apportionment rule " + process.Apportionment);
            }
            List<double> weights = new List<double>(process.Outputs.Count);
            foreach (Quantity produced in process.Outputs)
            {
                weights.Add(Weight(produced, mass));
            }
            double total = CompensatedSum.Of(weights);
            if (total <= Epsilon)
            {
                return 1.0 / process.Outputs.Count;
            }
            return Weight(new Quantity(commodity, amount), mass) / total;
        }

        private static double Weight(Quantity produced, Dictionary<string, double> mass)
        {
            double perUnit;
            if (!mass.TryGetValue(produced.Name, out perUnit))
            {
                perUnit = 1.0;
            }
            return perUnit * produced.Amount;
        }

        private static List<string> SortedOutputNames(ProcessSpec process)
        {
            List<string> names = new List<string>(process.Outputs.Count);
            foreach (Quantity produced in process.Outputs)
            {
                names.Add(produced.Name);
            }
            names.Sort(string.CompareOrdinal);
            return names;
        }

        private static List<Quantity> SortedOutputs(ProcessSpec process)
        {
            List<Quantity> outputs = new List<Quantity>(process.Outputs);
            outputs.Sort(CompareByName);
            return outputs;
        }

        private static int CompareByName(Quantity left, Quantity right)
        {
            return string.CompareOrdinal(left.Name, right.Name);
        }
    }
}
