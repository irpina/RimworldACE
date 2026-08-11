"""Validate value_model against RimWorld's Item And Building Acquisition table.

Cases transcribed from a dev-mode export (Debug output -> Economy -> Item And
Building Acquisition). Two independent checks:

  BASE   - the game's BaseMarketValue, i.e. what value_model.base_market_value
           must reproduce. Covers authored values, derived values, and the
           roundToFiveOver=200 boundary in both directions.
  CALC   - the game's "calculated market value" column, present only for defs
           that have an authored value *and* a computable cost. That is
           exactly the override set from docs/03-overrides.md, so this checks
           the whole overrides analysis against the game's own arithmetic.

Finding this table is what exposed roundToFiveOver: MarketValue inherits it
from the abstract MarketValueBase, so reading the raw node misses it.
"""
import sys

from value_model import Model

# defName -> game's base market value
BASE = {
    # --- below the rounding threshold, must stay exact ---
    "Steel": 1.9, "WoodLog": 1.2, "Cloth": 1.5, "Silver": 1.0, "Gold": 10.0,
    "Plasteel": 9.0, "Uranium": 6.0, "Jade": 5.0, "Chemfuel": 2.3,
    "ComponentIndustrial": 32.0, "BlocksGranite": 0.9, "Leather_Plain": 2.1,
    "MealSimple": 15.0, "MealFine": 20.0, "MealLavish": 40.0,
    "Kibble": 1.1, "Pemmican": 1.4, "Hay": 0.6, "Milk": 1.9,
    "WoolSheep": 2.7, "EggChickenUnfertilized": 7.0, "Neutroamine": 6.0,
    "MedicineHerbal": 10.0, "MedicineIndustrial": 18.0, "Penoxycyline": 18.0,
    "Yayo": 21.0, "Flake": 14.0, "WakeUp": 35.0, "GoJuice": 53.0,
    "PsychiteTea": 10.0, "SmokeleafJoint": 11.0, "GravlitePanel": 4.0,
    "Shell_HighExplosive": 55.0, "Shell_EMP": 55.0, "Shell_Deadlife": 55.0,
    "Gun_Revolver": 135.4, "Gun_Autopistol": 139.0,
    "Bow_Short": 44.6, "Pila": 109.2, "Bow_Great": 104.4,
    "VoidsightSerum": 60.0, "GhoulResurrectionSerum": 60.0,
    "MindNumbSerum": 80.0, "AdrenalHeart": 94.5, "NerveSpiker": 62.4,
    # --- above 200: rounded to the nearest 5 ---
    "Gun_MachinePistol": 220.0, "Gun_BoltActionRifle": 255.0,
    "Gun_AssaultRifle": 480.0, "Gun_SniperRifle": 530.0, "Gun_Minigun": 1160.0,
    "Gun_ChargeRifle": 1010.0, "Gun_ChargeLance": 1355.0,
    "Gun_HeavySMG": 355.0, "Gun_LMG": 425.0, "Gun_ChainShotgun": 405.0,
    "Gun_EmpLauncher": 505.0, "Gun_IncendiaryLauncher": 340.0,
    "Weapon_GrenadeFrag": 265.0, "Weapon_GrenadeEMP": 315.0,
    "BionicEye": 1030.0, "BionicArm": 1030.0, "BionicStomach": 785.0,
    "BionicTongue": 565.0, "AestheticNose": 585.0, "GastroAnalyzer": 830.0,
    "ArmorskinGland": 1475.0, "StoneskinGland": 1920.0, "VacskinGland": 1230.0,
    "SimpleProstheticArm": 260.0, "PowerClaw": 385.0, "CochlearImplant": 220.0,
    "Apparel_PowerArmor": 2035.0, "Apparel_ArmorRecon": 1540.0,
    "Apparel_ArmorCataphract": 3120.0, "Apparel_MechlordSuit": 7015.0,
    "Apparel_ArmorCataphractPrestige": 3930.0,
    "Apparel_PowerArmorHelmet": 635.0, "Apparel_ShieldBelt": 390.0,
    "Apparel_Gunlink": 345.0, "Apparel_PackJump": 645.0,
    "ComponentSpacer": 200.0, "SubcoreBasic": 200.0,
    "MetalbloodSerum": 200.0, "JuggernautSerum": 200.0,
    "ControlSublink": 1200.0, "RepairProbe": 1200.0,
    "DetoxifierLung": 925.0, "DetoxifierKidney": 1080.0,
    "RevenantVertebrae": 1895.0, "BiomutationPulser": 800.0,
    "Apparel_BiomutationLance": 850.0, "Gun_BeamRepeater": 1235.0,
}

# defName -> game's "calculated market value" (the override set)
CALC = {
    "GravlitePanel": 25.5, "PsychiteTea": 9.0, "SmokeleafJoint": 8.0,
    "Flake": 8.5, "Penoxycyline": 14.2, "MedicineIndustrial": 23.0,
    "Yayo": 16.5, "WakeUp": 15.2, "GoJuice": 35.2,
    "Shell_HighExplosive": 63.0, "Shell_Incendiary": 65.0,
    "Shell_EMP": 92.5, "Shell_Smoke": 47.5, "Shell_Firefoam": 47.5,
    "Shell_Toxic": 42.0, "Shell_Deadlife": 18.8,
    "VoidsightSerum": 19.5, "GhoulResurrectionSerum": 25.0,
    "MindNumbSerum": 34.5, "MetalbloodSerum": 20.0, "JuggernautSerum": 17.5,
    "SubcoreBasic": 169.8, "OxygenPump": 261.2,
    "BiomutationPulser": 514.1, "Apparel_BiomutationLance": 523.1,
    "DetoxifierLung": 1028.6, "DetoxifierKidney": 628.6,
    "ControlSublink": 639.5, "ControlSublinkHigh": 1707.5,
    "RemoteRepairer": 1203.5, "MechFormfeeder": 703.5,
    "RemoteShielder": 1203.5, "RepairProbe": 1911.5,
}
TOL = 0.01


def main():
    m = Model()
    fails = []

    ok = 0
    for d, want in BASE.items():
        got = m.base_market_value(d)
        if abs(got - want) <= max(0.05, TOL * abs(want)):
            ok += 1
        else:
            fails.append(("base", d, got, want))
    print(f"  {'OK ' if ok == len(BASE) else 'FAIL'} base market value   "
          f"{ok}/{len(BASE)} within {TOL*100:.0f}%")

    ok2 = 0
    for d, want in CALC.items():
        _, _, got = m.breakdown(d)
        if abs(got - want) <= max(0.05, TOL * abs(want)):
            ok2 += 1
        else:
            fails.append(("calculated", d, got, want))
    print(f"  {'OK ' if ok2 == len(CALC) else 'FAIL'} calculated value    "
          f"{ok2}/{len(CALC)} within {TOL*100:.0f}%")

    if fails:
        print(f"\n{len(fails)} mismatches:")
        for what, d, got, want in fails:
            print(f"    {what:11} {d:34} ours={got:10.2f} game={want:10.2f}")
        return 1
    print("\nall checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
