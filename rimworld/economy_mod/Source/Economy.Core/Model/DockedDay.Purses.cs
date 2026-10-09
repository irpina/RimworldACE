using System.Collections.Generic;

namespace SocialProduction.Economy.Core.Model
{
    public static partial class DockedDay
    {
        /// <summary><c>_settle_purses</c> (docs/55) with rule two, retained
        /// earnings built into capacity (docs/132 s3).</summary>
        public static void SettlePurses(EconomyState e)
        {
            for (int r = 0; r < e.Regions.Count; r++)
            {
                Region region = e.Regions.ValueAt(r);
                foreach (Producer producer in region.Producers)
                {
                    if (!producer.Active)
                    {
                        continue;
                    }
                    if (e.BankruptcyIdleDays > 0 && producer.LiquidityIdleDays >= e.BankruptcyIdleDays)
                    {
                        Bankrupt(e, region, producer);
                        continue;
                    }
                    producer.CashTarget = e.WorkingCapitalDays * DailyOutlay(e, producer, region);
                    if (producer.Cash > producer.CashTarget)
                    {
                        double excess = producer.Cash - producer.CashTarget;
                        producer.Cash = producer.CashTarget;
                        if (e.Accumulate && producer.Process.CapitalBill.Count == 0)
                        {
                            double retained = excess * e.RetentionRate;
                            double unit = BillFreeConstructionUnit(e, producer, region);
                            if (retained > 0.0 && unit > Epsilon)
                            {
                                producer.CapacityPerDay += retained / unit;
                                region.Cash += retained;
                                Add(e.Ledger.ConstructionWages, region.Name, retained);
                                excess -= retained;
                            }
                        }
                        region.Cash += excess;
                        producer.DistributedTotal += excess;
                        Add(e.Ledger.Distributions, region.Name, excess);
                    }
                }
            }
        }

        /// <summary><c>_bankrupt</c>: capacity lost, the purse back to the fund.</summary>
        private static void Bankrupt(EconomyState e, Region region, Producer producer)
        {
            Add(e.Ledger.CapacityLost, producer.Commodity, producer.CapacityPerDay);
            Bankruptcy record = new Bankruptcy();
            record.Day = e.Day;
            record.Region = region.Name;
            record.Producer = producer.Name;
            e.Ledger.Bankruptcies.Add(record);
            Retire(region, producer);
        }

        /// <summary><c>_retire</c>, without procurement.</summary>
        private static void Retire(Region region, Producer producer)
        {
            producer.CapacityPerDay = 0.0;
            producer.Active = false;
            region.Cash += producer.Cash;
            producer.Cash = 0.0;
        }

        /// <summary><c>_daily_outlay</c>: a day at full capacity, in cash.</summary>
        internal static double DailyOutlay(EconomyState e, Producer producer, Region region)
        {
            double runs = Lab.RunsFor(producer.Process, producer.CapacityPerDay);
            return runs * OutlayPerRun(producer, region) + PlantMatterCost(e, producer, region);
        }

        /// <summary><c>_outlay_per_run</c>: inputs at regional prices, and wages.</summary>
        internal static double OutlayPerRun(Producer producer, Region region)
        {
            double wagePerTick = region.SubsistenceBasket.Count > 0
                ? Lab.WageRate(region) / Lab.Max(region.TicksPerWorkerDay, Epsilon)
                : 0.0;
            return Lab.InputCostPerRun(producer.Process, region.Prices)
                + producer.Process.DirectLabor * wagePerTick;
        }

        /// <summary><c>_plant_matter_cost</c>: zero for a process without a bill.</summary>
        internal static double PlantMatterCost(EconomyState e, Producer producer, Region region)
        {
            OrderedMap<double> bill = Lab.CapitalBillPerCapacity(producer.Process);
            if (bill.Count == 0 || producer.CapacityPerDay <= Epsilon)
            {
                return 0.0;
            }
            double perCapacity = producer.CapacityPerDay / Lab.Max(e.CapitalServiceLifeDays, Epsilon);
            List<double> materials = new List<double>(bill.Count);
            for (int i = 0; i < bill.Count; i++)
            {
                materials.Add(perCapacity * bill.ValueAt(i) * region.Prices.Get(bill.KeyAt(i), 0.0));
            }
            double wagePerTick = region.SubsistenceBasket.Count > 0
                ? Lab.WageRate(region) / Lab.Max(region.TicksPerWorkerDay, Epsilon)
                : 0.0;
            double construction = perCapacity
                * producer.Process.MachinesPerCapacity
                * producer.Process.CapitalConstructionLabor
                * wagePerTick;
            return Lab.Sum(materials) + construction;
        }

        /// <summary><c>_bill_free_construction_unit</c> (docs/132 s3).</summary>
        internal static double BillFreeConstructionUnit(EconomyState e, Producer producer, Region region)
        {
            return Lab.EffectiveUnitCost(producer, region.Prices) * e.ConstructionCostMultiplier;
        }
    }
}
