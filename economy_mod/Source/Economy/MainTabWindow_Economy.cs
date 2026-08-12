using RimWorld;
using UnityEngine;
using Verse;

namespace SocialProduction.Economy
{
    public sealed class MainTabWindow_Economy : MainTabWindow
    {
        public override Vector2 RequestedTabSize => new Vector2(620f, 360f);

        public override void DoWindowContents(Rect inRect)
        {
            EconomyWorldComponent economy = Find.World?.GetComponent<EconomyWorldComponent>();

            Text.Font = GameFont.Medium;
            Widgets.Label(new Rect(inRect.x, inRect.y, inRect.width, 35f), "World economy");

            Text.Font = GameFont.Small;
            float y = inRect.y + 48f;
            DrawRow(inRect, ref y, "Mode", "Read-only observation");
            DrawRow(inRect, ref y, "Vanilla prices", "Unchanged");
            DrawRow(inRect, ref y, "Economy days simulated", economy == null ? "Unavailable" : economy.CompletedDays.ToString());
            DrawRow(inRect, ref y, "Settlements observed", economy == null ? "Unavailable" : economy.ObservedSettlementCount.ToString());

            y += 18f;
            Widgets.Label(
                new Rect(inRect.x, y, inRect.width, 80f),
                "This is the Stage 1 runtime shell. Regional commodity markets will appear here as the deterministic Stage 0 model is integrated.");
        }

        private static void DrawRow(Rect bounds, ref float y, string label, string value)
        {
            Widgets.Label(new Rect(bounds.x, y, 250f, 28f), label);
            Widgets.Label(new Rect(bounds.x + 260f, y, bounds.width - 260f, 28f), value);
            y += 30f;
        }
    }
}
