using System;
using System.Collections.Generic;

namespace SocialProduction.Economy.Core
{
    /// <summary>
    /// One atomic unit of the economy's day.
    ///
    /// Atomic is the whole point (docs/82 section 2): the scheduler may
    /// break between phases and never inside one, because a phase
    /// interrupted halfway would let the next tick read state it is
    /// midway through writing. A phase that cannot be run to completion
    /// in one go does not belong here.
    /// </summary>
    public interface IDayPhase
    {
        string Name { get; }
        void Execute();
    }

    /// <summary>A phase built from a delegate, for phases with no state of their own.</summary>
    public sealed class DayPhase : IDayPhase
    {
        private readonly Action run;

        public DayPhase(string name, Action run)
        {
            Name = name;
            this.run = run;
        }

        public string Name { get; private set; }

        public void Execute()
        {
            run();
        }
    }

    /// <summary>
    /// Spread the economy's day across the game's ticks without changing
    /// what the day does (docs/82).
    ///
    /// The invariant, and the reason this class is worth its own
    /// document: **a day spread over any number of ticks produces exactly
    /// the state that day produces in one tick** — the same bits, not a
    /// tolerance. Every result in this project is a bit-level claim and
    /// an amortiser that perturbed the last bit would unpick all of them.
    ///
    /// So the scheduler decides only *when* to stop, never *what* to do
    /// next. The phase order is fixed, the cursor advances by one
    /// completed phase, and the budget — which is wall-clock and
    /// therefore varies — cannot change the sequence or its content. That
    /// is what makes the invariant testable: run the same day at every
    /// budget and compare.
    ///
    /// The cursor is saved state. A save can land mid-day, and re-running
    /// a phase is not harmless: the wage settlement pays a wage bill.
    /// </summary>
    public sealed class DayScheduler
    {
        private readonly List<IDayPhase> phases;
        private int cursor;
        private readonly List<string> executed = new List<string>();

        public DayScheduler(IEnumerable<IDayPhase> phases)
        {
            this.phases = new List<IDayPhase>(phases);
            if (this.phases.Count == 0)
            {
                throw new ArgumentException("a day needs at least one phase");
            }
        }

        /// <summary>Which phase runs next; part of the saved state.</summary>
        public int Cursor
        {
            get { return cursor; }
        }

        public int PhaseCount
        {
            get { return phases.Count; }
        }

        /// <summary>True when the day has no phases left to run.</summary>
        public bool DayComplete
        {
            get { return cursor >= phases.Count; }
        }

        /// <summary>
        /// The phases executed since the last <see cref="BeginDay"/>, in
        /// order. Kept so that the sequence itself can be compared across
        /// budgets and not only the state it leaves (docs/82 section 5.2).
        /// </summary>
        public IList<string> Executed
        {
            get { return executed; }
        }

        /// <summary>Start a day. The scheduler never begins one before the last finished.</summary>
        public void BeginDay()
        {
            if (!DayComplete && executed.Count > 0)
            {
                throw new InvalidOperationException(
                    "a day is still in progress at phase " + phases[cursor].Name);
            }
            cursor = 0;
            executed.Clear();
        }

        /// <summary>
        /// Restore a day interrupted by a save, at the phase it had
        /// reached. The phases already applied are not re-run.
        /// </summary>
        public void ResumeAt(int savedCursor)
        {
            if (savedCursor < 0 || savedCursor > phases.Count)
            {
                throw new ArgumentOutOfRangeException("savedCursor");
            }
            cursor = savedCursor;
            executed.Clear();
        }

        /// <summary>
        /// Run up to <paramref name="phaseBudget"/> phases, stopping at the
        /// end of the day. Returns how many ran.
        ///
        /// The budget is a count here rather than a duration so the
        /// invariant can be tested exhaustively; the game side converts
        /// its wall-clock budget into this before calling, which keeps the
        /// clock out of the part that has to be deterministic.
        /// </summary>
        public int AdvanceTick(int phaseBudget)
        {
            if (phaseBudget <= 0)
            {
                return 0;
            }
            int ran = 0;
            while (ran < phaseBudget && cursor < phases.Count)
            {
                IDayPhase phase = phases[cursor];
                phase.Execute();
                executed.Add(phase.Name);
                cursor++;
                ran++;
            }
            return ran;
        }

        /// <summary>
        /// Finish the day whatever is left of it, which is what a catch-up
        /// after skipped ticks does and what the one-tick day did before
        /// this class existed.
        /// </summary>
        public int RunWholeDay()
        {
            return AdvanceTick(phases.Count - cursor);
        }
    }
}
