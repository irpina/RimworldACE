// A façade of exactly the RimWorld and Unity API surface this mod uses.
//
// **Not shipped, and never referenced by a real build.** It exists so the
// game-facing code can be *compiled* on a machine that does not have
// RimWorld's managed assemblies — which are game files, not redistributable
// — and it is in the repository rather than a scratchpad because it is
// only trustworthy if it is maintained.
//
// Every type and member here was read out of the previously built
// `1.6/Assemblies/SocialProduction.Economy.dll` with `monodis --typeref`
// and `--memberref` (docs/87). That assembly was compiled against the real
// RimWorld 1.6.9676.17924, so its reference tables are ground truth for
// the surface the mod actually touches — which is why the namespaces here
// are right where a hand-written guess had `Faction` in the wrong one.
//
// What this catches: syntax, types, call shapes, and any use of a member
// the last real build did not use. What it cannot catch: a member whose
// real signature differs from the shape inferred here, and anything about
// behaviour. A build against the real assemblies is still required and is
// still the first thing a session at the game should do.
using System.Collections.Generic;

namespace Verse
{
    public enum LookMode { Undefined, Value, Deep, Reference, Def, LocalTargetInfo, TargetInfo, GlobalTargetInfo, BodyPart }
    public enum LoadSaveMode { Inactive, Saving, LoadingVars, ResolvingCrossRefs, PostLoadInit }
    public enum GameFont { Tiny, Small, Medium }

    public class Def { public string defName; }

    public interface IExposable { void ExposeData(); }

    public static class Scribe { public static LoadSaveMode mode; }

    public static class Scribe_Values
    {
        public static void Look<T>(ref T value, string label, T defaultValue = default(T), bool forceSave = false) { }
    }

    public static class Scribe_Collections
    {
        public static void Look<T>(ref List<T> list, string label, LookMode lookMode = LookMode.Undefined, params object[] ctorArgs) { }
    }

    public static class Log
    {
        public static void Message(string text) { }
        public static void Warning(string text) { }
        public static void Error(string text) { }
    }

    public class TickManager { public int TicksGame { get { return 0; } } }

    public static class Find
    {
        public static TickManager TickManager { get { return null; } }
        public static RimWorld.Planet.World World { get { return null; } }
        public static RimWorld.Planet.WorldObjectsHolder WorldObjects { get { return null; } }
        public static RimWorld.Planet.WorldGrid WorldGrid { get { return null; } }
    }

    public static class Text { public static GameFont Font { set { } } }

    public static class Widgets
    {
        public static void Label(UnityEngine.Rect rect, string label) { }
        public static void DrawLineHorizontal(float x, float y, float length) { }
        public static void BeginScrollView(
            UnityEngine.Rect outRect, ref UnityEngine.Vector2 scrollPosition,
            UnityEngine.Rect viewRect, bool showScrollbars = true) { }
        public static void EndScrollView() { }
    }
}

namespace UnityEngine
{
    public struct Color
    {
        public float r, g, b, a;
        public Color(float r, float g, float b) { this.r = r; this.g = g; this.b = b; this.a = 1f; }
        public static Color white { get { return new Color(1f, 1f, 1f); } }
    }

    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public static Vector2 zero { get { return new Vector2(0f, 0f); } }
    }

    public struct Rect
    {
        private float xv, yv, wv, hv;
        public Rect(float x, float y, float width, float height)
        { xv = x; yv = y; wv = width; hv = height; }
        public float x { get { return xv; } set { xv = value; } }
        public float y { get { return yv; } set { yv = value; } }
        public float width { get { return wv; } set { wv = value; } }
        public float height { get { return hv; } set { hv = value; } }
    }

    public static class GUI { public static Color color { set { } } }
}

namespace RimWorld
{
    public class BiomeDef : Verse.Def { }

    public class Faction
    {
        public string Name { get { return null; } }
        public int loadID;
    }

    public class MainTabWindow
    {
        public virtual UnityEngine.Vector2 RequestedTabSize { get { return UnityEngine.Vector2.zero; } }
        public virtual void DoWindowContents(UnityEngine.Rect inRect) { }
    }
}

namespace RimWorld.Planet
{
    public enum Hilliness { Undefined, Flat, SmallHills, LargeHills, Mountainous, Impassable }

    public struct PlanetTile { public int tileId; }

    public class Tile
    {
        public RimWorld.BiomeDef PrimaryBiome { get { return null; } }
        public Hilliness hilliness;
    }

    public class WorldGrid { public Tile this[PlanetTile tile] { get { return null; } } }

    public class WorldInfo { public int persistentRandomValue; }

    public class World
    {
        public WorldInfo info;
        public T GetComponent<T>() where T : WorldComponent { return null; }
    }

    public class WorldComponent
    {
        public WorldComponent(World world) { }
        public virtual void FinalizeInit(bool fromLoad) { }
        public virtual void WorldComponentTick() { }
        public virtual void ExposeData() { }
    }

    public class WorldObject
    {
        public int ID;
        public PlanetTile Tile { get { return default(PlanetTile); } }
        public RimWorld.Faction Faction { get { return null; } }
    }

    public class Settlement : WorldObject { }

    public class WorldObjectsHolder
    {
        public List<Settlement> Settlements { get { return null; } }
    }
}
