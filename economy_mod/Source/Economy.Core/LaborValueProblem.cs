using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// One name and one quantity, in the order the laboratory holds them.
    ///
    /// The model's processes keep their outputs and inputs in insertion
    /// order, and the solve reads some of them in that order and some
    /// sorted; a list of pairs carries the first, and the solver sorts for
    /// the second.  A dictionary would lose the order the answer depends on.
    /// </summary>
    public struct Quantity
    {
        public readonly string Name;
        public readonly double Amount;

        public Quantity(string name, double amount)
        {
            Name = name;
            Amount = amount;
        }
    }

    /// <summary>
    /// A technology as the value solve sees it: the fields of the
    /// laboratory's <c>Process</c> the solve reads, and no others.
    /// </summary>
    public sealed class ProcessSpec
    {
        public string Name;
        public List<Quantity> Outputs = new List<Quantity>();
        public List<Quantity> Inputs = new List<Quantity>();
        public double DirectLabor;
        public string Apportionment = "mass";
        /// <summary>Authored embodied labor of the plant per unit of daily capacity.</summary>
        public double CapitalLaborPerCapacity;
        /// <summary>Department I: what one machine is made of (docs/36).</summary>
        public List<Quantity> CapitalBill = new List<Quantity>();
        public double CapitalConstructionLabor;
        public double MachinesPerCapacity;

        public double OutputOf(string commodity)
        {
            for (int i = 0; i < Outputs.Count; i++)
            {
                if (Outputs[i].Name == commodity)
                {
                    return Outputs[i].Amount;
                }
            }
            return 0.0;
        }
    }

    /// <summary>One active producer with its realized runs for the day.</summary>
    public sealed class Contributor
    {
        public string Region;
        public string Producer;
        public double Runs;
        public ProcessSpec Process;
    }

    /// <summary>
    /// Everything <c>Economy._update_labor_values</c> reads, in the order it
    /// reads it: regions in insertion order, producers in list order.
    /// </summary>
    public sealed class LaborValueProblem
    {
        public double Tolerance = 1e-12;
        public int MaxIterations = 1000;
        public double ServiceLifeDays = 600.0;
        /// <summary>Every commodity and its mass, in the economy's order.</summary>
        public List<Quantity> Commodities = new List<Quantity>();
        public List<string> Regions = new List<string>();
        public List<Contributor> Contributors = new List<Contributor>();
    }

    public sealed class LaborValueSolution
    {
        /// <summary>Social values, one per commodity, in the economy's order.</summary>
        public Dictionary<string, double> Values = new Dictionary<string, double>();
        /// <summary>Each region's individual values, for what it produced.</summary>
        public Dictionary<string, Dictionary<string, double>> RegionalValues =
            new Dictionary<string, Dictionary<string, double>>();
        /// <summary>Commodities nobody produced, whose values were carried over.</summary>
        public List<string> Stale = new List<string>();
        public int Iterations;
    }

    /// <summary>The solve did not converge: the input matrix is not productive.</summary>
    public sealed class NotProductiveException : System.Exception
    {
        public NotProductiveException(string message) : base(message)
        {
        }
    }
}
