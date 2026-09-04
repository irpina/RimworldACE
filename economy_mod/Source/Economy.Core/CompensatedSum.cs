using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// CPython's <c>sum()</c> over floats, exactly (docs/53 section 3).
    ///
    /// Since Python 3.12, <c>builtin_sum_impl</c>'s float path is
    /// Neumaier's compensated summation: a running total <c>f</c>, a
    /// running correction <c>c</c>, and <c>f += c</c> once at the end if
    /// <c>c</c> is non-zero and finite.  The laboratory's histories depend
    /// on it -- docs/33 found a <c>+=</c> loop and a <c>sum()</c> over the
    /// same terms differing in the last bit -- so the port has to use it
    /// where, and only where, the laboratory uses <c>sum()</c>.
    /// </summary>
    public static class CompensatedSum
    {
        public static double Of(IEnumerable<double> terms)
        {
            double f = 0.0;
            double c = 0.0;
            foreach (double x in terms)
            {
                double t = f + x;
                if (Math.Abs(f) >= Math.Abs(x))
                {
                    c += (f - t) + x;
                }
                else
                {
                    c += (x - t) + f;
                }
                f = t;
            }
            if (c != 0.0 && !double.IsInfinity(c) && !double.IsNaN(c))
            {
                f += c;
            }
            return f;
        }
    }
}
