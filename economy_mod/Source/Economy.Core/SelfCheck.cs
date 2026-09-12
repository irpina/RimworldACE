using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace SocialProduction.Economy.Core
{
    public enum CheckVerdict { Passed, Failed, Skipped }

    /// <summary>One thing the mod checked about itself, and what it saw.</summary>
    public sealed class Check
    {
        public string Name = "";
        public string Expected = "";
        public string Observed = "";
        public CheckVerdict Verdict = CheckVerdict.Skipped;
        public string Note = "";
    }

    /// <summary>
    /// What the mod found when it checked itself, rendered for a human to
    /// paste back (docs/88).
    ///
    /// The point is that the *game* produces the evidence. Every other
    /// claim in this project is a machine-produced number a later run can
    /// contradict; the in-game checks were the last ones that were a
    /// person's impression, and an impression is not reproducible, not
    /// precise, and cannot fail usefully — someone who does not know the
    /// mid-day resume exists will not notice that it did not happen.
    /// </summary>
    public sealed class SelfCheckReport
    {
        private readonly List<Check> checks = new List<Check>();

        public IList<Check> Checks { get { return checks; } }

        public SelfCheckReport Add(
            string name, string expected, string observed, CheckVerdict verdict, string note = "")
        {
            Check check = new Check();
            check.Name = name ?? "";
            check.Expected = expected ?? "";
            check.Observed = observed ?? "";
            check.Verdict = verdict;
            check.Note = note ?? "";
            checks.Add(check);
            return this;
        }

        public SelfCheckReport Expect(string name, string expected, string observed, string note = "")
        {
            return Add(name, expected, observed,
                expected == observed ? CheckVerdict.Passed : CheckVerdict.Failed, note);
        }

        public int Failures
        {
            get
            {
                int n = 0;
                foreach (Check check in checks) if (check.Verdict == CheckVerdict.Failed) n++;
                return n;
            }
        }

        public int Ran
        {
            get
            {
                int n = 0;
                foreach (Check check in checks) if (check.Verdict != CheckVerdict.Skipped) n++;
                return n;
            }
        }

        /// <summary>
        /// True only when checks actually ran and none failed.
        ///
        /// An empty report is **not** a pass. "No checks ran" and "all
        /// checks passed" are different states and the first has been
        /// mistaken for the second in every test suite ever written
        /// (docs/88 section 5.2).
        /// </summary>
        public bool Passed { get { return Ran > 0 && Failures == 0; } }

        public string Summary
        {
            get
            {
                if (Ran == 0)
                {
                    return "NO CHECKS RAN (" + checks.Count + " skipped)";
                }
                return Failures == 0
                    ? "all " + Ran + " checks passed"
                    : Failures + " of " + Ran + " checks FAILED";
            }
        }

        /// <summary>
        /// The report, in the order the checks were added — never a
        /// dictionary's order, so the same run renders the same text.
        /// </summary>
        public string Render()
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("[Social Production: Economy] self-check: ")
              .Append(Summary).Append('\n');
            foreach (Check check in checks)
            {
                sb.Append("  ").Append(Mark(check.Verdict)).Append(' ')
                  .Append(check.Name).Append(": expected ").Append(check.Expected)
                  .Append(", observed ").Append(check.Observed);
                if (check.Note.Length > 0)
                {
                    sb.Append("  -- ").Append(check.Note);
                }
                sb.Append('\n');
            }
            return sb.ToString();
        }

        private static string Mark(CheckVerdict verdict)
        {
            switch (verdict)
            {
                case CheckVerdict.Passed: return "PASS";
                case CheckVerdict.Failed: return "FAIL";
                default: return "skip";
            }
        }
    }
}
