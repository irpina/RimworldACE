using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace SocialProduction.Economy
{
    public sealed class MainTabWindow_Economy : MainTabWindow
    {
        private Vector2 scroll = Vector2.zero;

        public override Vector2 RequestedTabSize => new Vector2(760f, 520f);

        public override void DoWindowContents(Rect inRect)
        {
            EconomyWorldComponent economy =
                Find.World?.GetComponent<EconomyWorldComponent>();

            Text.Font = GameFont.Medium;
            Widgets.Label(
                new Rect(inRect.x, inRect.y, inRect.width, 35f), "World economy");

            Text.Font = GameFont.Small;
            float y = inRect.y + 44f;
            DrawRow(inRect, ref y, "Mode", "Read-only observation");
            DrawRow(inRect, ref y, "Vanilla prices", "Unchanged");
            DrawRow(
                inRect, ref y, "Economy days simulated",
                economy == null ? "Unavailable" : economy.CompletedDays.ToString());
            DrawRow(
                inRect, ref y, "Settlements observed",
                economy == null ? "Unavailable" : economy.ObservedSettlementCount.ToString());
            DrawRow(
                inRect, ref y, "Regions",
                economy == null ? "Unavailable" : economy.RegionCount.ToString());
            DrawRow(
                inRect, ref y, "Reload determinism",
                economy == null ? "Unavailable" : economy.DeterminismStatus);

            y += 12f;
            Widgets.DrawLineHorizontal(inRect.x, y, inRect.width);
            y += 10f;

            if (economy == null || economy.Profiles.Count == 0)
            {
                Widgets.Label(
                    new Rect(inRect.x, y, inRect.width, 60f),
                    "No settlement profiles yet.");
                return;
            }

            // Grouped by region, and both the regions and the settlements
            // within them are walked in the order ProfileBuilder assigned,
            // so the table reads the same way twice.
            List<SettlementProfile> profiles =
                new List<SettlementProfile>(economy.Profiles);
            profiles.Sort(
                (a, b) =>
                {
                    int byRegion = a.RegionId.CompareTo(b.RegionId);
                    return byRegion != 0
                        ? byRegion
                        : a.TileId.CompareTo(b.TileId);
                });

            Rect viewport = new Rect(inRect.x, y, inRect.width, inRect.height - y);
            Rect content = new Rect(
                0f, 0f, viewport.width - 20f, profiles.Count * 24f + 30f);
            Widgets.BeginScrollView(viewport, ref scroll, content);
            float row = 0f;
            GUI.color = new Color(0.7f, 0.7f, 0.7f);
            DrawProfileRow(content, ref row, "region", "faction", "tile", "biome", "hilliness");
            GUI.color = Color.white;
            foreach (SettlementProfile profile in profiles)
            {
                DrawProfileRow(
                    content,
                    ref row,
                    profile.RegionId == ProfileBuilder.UnaffiliatedRegion
                        ? "-"
                        : profile.RegionId.ToString(),
                    profile.FactionName ?? "unaffiliated",
                    profile.TileId.ToString(),
                    profile.Biome ?? "-",
                    profile.Hilliness ?? "-");
            }
            Widgets.EndScrollView();
        }

        private static void DrawProfileRow(
            Rect bounds,
            ref float y,
            string region,
            string faction,
            string tile,
            string biome,
            string hilliness)
        {
            float x = bounds.x;
            Widgets.Label(new Rect(x, y, 60f, 24f), region);
            Widgets.Label(new Rect(x + 60f, y, 240f, 24f), faction);
            Widgets.Label(new Rect(x + 300f, y, 80f, 24f), tile);
            Widgets.Label(new Rect(x + 380f, y, 200f, 24f), biome);
            Widgets.Label(new Rect(x + 580f, y, 140f, 24f), hilliness);
            y += 24f;
        }

        private static void DrawRow(
            Rect bounds, ref float y, string label, string value)
        {
            Widgets.Label(new Rect(bounds.x, y, 250f, 26f), label);
            Widgets.Label(
                new Rect(bounds.x + 260f, y, bounds.width - 260f, 26f), value);
            y += 28f;
        }
    }
}
