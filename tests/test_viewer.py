"""The laboratory viewer (docs/48): it reads, it is deterministic, and it
never touches the model."""

import json
import threading
import unittest
import urllib.request
from urllib.error import HTTPError

from economy_lab.scenarios import ScenarioParameters, demand_boom
from economy_lab.viewer import catalog, markdown
from economy_lab.viewer.runs import (
    OverrideError,
    RunCache,
    coerce_options,
    coerce_overrides,
    document_bytes,
    run_document,
    run_key,
)
from economy_lab.viewer.server import make_server, parameter_listing


class CatalogTests(unittest.TestCase):
    def test_every_scenario_function_is_catalogued(self):
        expected = {
            "equilibrium", "regional_glut", "producer_loss", "arbitrage",
            "input_shortage", "reserve_depletion", "subsistence_shock",
            "technique_change", "cost_competition", "generous_basket",
            "perishable_meals", "capital_goods", "capacity_exit",
            "recreation_basket", "recreation_sweep", "demand_boom",
            "wage_slump", "reserve_army_sweep", "boom_reversal", "cash_circuit",
            "gravitation",
        }
        self.assertEqual(set(catalog.CATALOG), expected)

    def test_options_are_read_off_the_signatures(self):
        names = [o.name for o in catalog.CATALOG["demand_boom"].options]
        self.assertEqual(names, ["days_after_boom", "bargaining", "habituation", "labor_pool"])
        types = {o.name: o.type for o in catalog.CATALOG["demand_boom"].options}
        self.assertEqual(types["bargaining"], "bool")
        self.assertEqual(types["labor_pool"], "float?")
        self.assertEqual(types["days_after_boom"], "int")

    def test_every_scenario_names_its_documents(self):
        for scenario in catalog.CATALOG.values():
            self.assertTrue(scenario.docs, scenario.name)
            for number in scenario.docs:
                self.assertTrue(
                    list(catalog.DOCS_DIR.glob(f"{number:02d}-*.md")),
                    f"{scenario.name} names docs/{number}, which does not exist",
                )

    def test_the_slow_scenario_is_marked(self):
        self.assertEqual(catalog.CATALOG["capacity_exit"].cost, "slow")
        self.assertEqual(catalog.CATALOG["demand_boom"].cost, "fast")

    def test_the_parameter_listing_covers_every_field(self):
        rows = parameter_listing()
        from dataclasses import fields

        self.assertEqual(
            [row["name"] for row in rows],
            [field.name for field in fields(ScenarioParameters)],
        )
        groups = {row["name"]: row["group"] for row in rows}
        self.assertIn("docs/46", groups["wage_bargaining_strength"])
        self.assertEqual(groups["reference_price"], "market and calibration")


class OverrideTests(unittest.TestCase):
    def test_unknown_names_are_refused(self):
        with self.assertRaises(OverrideError):
            coerce_overrides({"no_such_parameter": 1.0})

    def test_integers_stay_integers_and_floats_are_refused_for_them(self):
        self.assertEqual(coerce_overrides({"technique_change_day": "70"}), {"technique_change_day": 70})
        self.assertIsInstance(coerce_overrides({"technique_change_day": 70.0})["technique_change_day"], int)
        with self.assertRaises(OverrideError):
            coerce_overrides({"technique_change_day": 70.5})

    def test_booleans_and_floats_are_read_from_strings(self):
        self.assertEqual(coerce_overrides({"capital_goods": "true"}), {"capital_goods": True})
        self.assertEqual(coerce_overrides({"boom_demand_multiplier": "1.5"}), {"boom_demand_multiplier": 1.5})
        with self.assertRaises(OverrideError):
            coerce_overrides({"capital_goods": "maybe"})

    def test_options_are_checked_against_the_scenario(self):
        scenario = catalog.CATALOG["demand_boom"]
        self.assertEqual(
            coerce_options(scenario, {"bargaining": "true", "labor_pool": "inf", "days_after_boom": "10"}),
            {"bargaining": True, "days_after_boom": 10, "labor_pool": float("inf")},
        )
        self.assertEqual(coerce_options(scenario, {"labor_pool": ""}), {})
        with self.assertRaises(OverrideError):
            coerce_options(scenario, {"route_capacity": 1.0})


class RunDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.without = run_document("demand_boom", {"days_after_boom": 40})
        cls.with_rule = run_document("demand_boom", {"days_after_boom": 40, "bargaining": True})

    def test_the_same_key_gives_the_same_bytes(self):
        again = run_document("demand_boom", {"days_after_boom": 40})
        self.assertEqual(document_bytes(self.without), document_bytes(again))
        self.assertEqual(self.without["key"], again["key"])
        self.assertNotEqual(self.without["key"], self.with_rule["key"])

    def test_the_key_is_canonical(self):
        self.assertEqual(
            run_key("demand_boom", {"bargaining": True, "days_after_boom": 40}, {}),
            run_key("demand_boom", {"days_after_boom": 40, "bargaining": True}, {}),
        )

    def test_series_are_read_from_the_history_untouched(self):
        economy = demand_boom(40)
        expected = economy.series("Dust Basin", "meals")
        self.assertEqual(self.without["regions"]["Dust Basin"]["price"]["meals"], expected)
        self.assertEqual(self.without["days"], list(range(len(expected))))
        self.assertEqual(self.without["shock_day"], 60)

    def test_the_run_is_json_without_nan(self):
        json.dumps(self.with_rule, allow_nan=False)

    def test_the_five_ledgers_carry_their_units_apart(self):
        ledgers = self.with_rule["ledgers"]
        self.assertEqual(set(ledgers), {"labor_value", "market_price", "price_of_production", "surplus_value", "rent"})
        self.assertEqual(ledgers["labor_value"]["unit"], "work-ticks")
        self.assertEqual(ledgers["market_price"]["unit"], "silver")
        self.assertEqual(ledgers["surplus_value"]["unit"], "work-ticks")
        # The money margin lives in the price panel and nowhere else.
        self.assertIn("margin", ledgers["market_price"]["regions"]["Dust Basin"]["decomposition"]["meals"])
        self.assertNotIn("margin", json.dumps(ledgers["surplus_value"]))

    def test_the_summary_is_the_terminal_runners(self):
        from economy_lab.scenarios import summary

        self.assertEqual(self.without["summary"], summary(demand_boom(40)))

    def test_a_sampled_history_is_carried_by_its_own_days(self):
        document = run_document("equilibrium", {"days": 20}, {"history_every": 5})
        self.assertEqual(document["days"], [0, 5, 10, 15, 20])
        self.assertEqual(len(document["regions"]["Dust Basin"]["price"]["yayo"]), 5)
        # The terminal summary indexes positionally and refuses; the ledgers
        # do not need it and are still there.
        self.assertIsNone(document["summary"])
        self.assertIn("no series", document["summary_unavailable"])
        self.assertIn("surplus_value", document["ledgers"])

    def test_the_derived_shock_day_is_the_exhaustion_day(self):
        document = run_document("reserve_depletion", {"days": 120})
        self.assertEqual(document["shock_day"], 100)

    def test_sweeps_return_rows(self):
        document = run_document("reserve_army_sweep")
        self.assertEqual(document["kind"], "sweep")
        pools = [row["labor_pool"] for row in document["sweep"]["rows"]]
        self.assertEqual(pools, [1.0, 0.5, "inf"])
        self.assertEqual(document["sweep"]["rows"][2]["premium_peak"], 0.0)

    def test_the_cache_returns_the_same_object(self):
        cache = RunCache()
        first = cache.get("equilibrium", {"days": 10}, {})
        second = cache.get("equilibrium", {"days": 10.0}, {})
        self.assertIs(first, second)
        self.assertEqual([row["key"] for row in cache.listing()], [first["key"]])


class MarkdownTests(unittest.TestCase):
    def test_headings_paragraphs_and_emphasis(self):
        html = markdown.render("# Title\n\nSome **bold** and *italic* text with `code`.\n")
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn("<code>code</code>", html)

    def test_tables_with_alignment(self):
        html = markdown.render("| a | b |\n|---|---:|\n| 1 | 2 |\n")
        self.assertIn("<table>", html)
        self.assertIn('<td style="text-align:right">2</td>', html)

    def test_lists_and_nesting(self):
        html = markdown.render("- one\n- two\n  - nested\n\n1. first\n2. second\n")
        self.assertIn("<ul><li>one</li><li>two<ul><li>nested</li></ul></li></ul>", html)
        self.assertIn("<ol><li>first</li><li>second</li></ol>", html)

    def test_code_fences_are_escaped_verbatim(self):
        html = markdown.render("```python\nif a < b: **x**\n```\n")
        self.assertIn("<pre><code class=\"language-python\">if a &lt; b: **x**</code></pre>", html)

    def test_document_references_become_links(self):
        html = markdown.render("See `docs/47` and docs/46 section 3.")
        self.assertIn('<a href="#doc/47"><code>docs/47</code></a>', html)
        self.assertIn('<a href="#doc/46">docs/46</a>', html)

    def test_html_in_the_source_is_escaped(self):
        html = markdown.render("<script>alert(1)</script>")
        self.assertNotIn("<script>", html)

    def test_every_document_renders(self):
        for path in sorted(catalog.DOCS_DIR.glob("*.md")):
            html = markdown.render(path.read_text(encoding="utf-8"))
            self.assertIn("<h1>", html, path.name)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as response:
            return json.loads(response.read().decode("utf-8"))

    def post(self, path, payload):
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_the_page_is_served(self):
        with urllib.request.urlopen(self.base + "/") as response:
            body = response.read().decode("utf-8")
        self.assertIn("Economy laboratory", body)
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")

    def test_static_files_cannot_escape_their_directory(self):
        with self.assertRaises(HTTPError) as caught:
            urllib.request.urlopen(self.base + "/static/../runs.py")
        self.assertEqual(caught.exception.code, 404)
        caught.exception.close()

    def test_the_catalog_and_parameters(self):
        scenarios = self.get("/api/scenarios")
        self.assertEqual(len(scenarios), 21)
        boom = next(s for s in scenarios if s["name"] == "demand_boom")
        self.assertEqual(boom["docs"], [46, 47])
        self.assertEqual(boom["shock"], 60)
        self.assertEqual(len(self.get("/api/parameters")), len(parameter_listing()))

    def test_a_run_with_and_without_bargaining(self):
        without = self.post("/api/run", {"scenario": "demand_boom", "options": {"days_after_boom": 150}})
        with_rule = self.post(
            "/api/run",
            {"scenario": "demand_boom", "options": {"days_after_boom": 150, "bargaining": "true"}},
        )
        self.assertNotEqual(without["key"], with_rule["key"])
        premium = with_rule["regions"]["Dust Basin"]["wage_premium"]
        self.assertGreater(max(premium), 0.0)
        self.assertEqual(max(without["regions"]["Dust Basin"]["wage_premium"]), 0.0)
        listing = self.get("/api/runs")
        self.assertEqual({row["key"] for row in listing} >= {without["key"], with_rule["key"]}, True)
        self.assertEqual(self.get(f"/api/runs/{without['key']}")["key"], without["key"])

    def test_bad_requests_are_400s(self):
        for payload in (
            {"scenario": "nowhere"},
            {"scenario": "equilibrium", "overrides": {"no_such": 1}},
            {"scenario": "equilibrium", "options": {"days": "ten"}},
        ):
            with self.assertRaises(HTTPError) as caught:
                self.post("/api/run", payload)
            self.assertEqual(caught.exception.code, 400)
            self.assertIn("error", json.loads(caught.exception.read().decode("utf-8")))

    def test_the_reference_metrics_and_the_sweep_are_served(self):
        metrics = self.get("/api/metrics")["metrics"]
        from economy_lab.baseline import DEFAULT_REFERENCE

        frozen = json.loads(DEFAULT_REFERENCE.read_text(encoding="utf-8"))["metrics"]
        self.assertEqual(len(metrics), len(frozen))
        ranking = self.get("/api/sensitivity")
        self.assertTrue(ranking["available"])
        self.assertEqual(ranking["ranking"][0]["parameter"], "ticks_per_worker_day")
        detail = self.get("/api/sensitivity/ticks_per_worker_day")
        self.assertTrue(detail["readings"])

    def test_documents_are_listed_and_rendered(self):
        documents = self.get("/api/docs")
        self.assertGreaterEqual(len(documents), 48)
        rendered = self.get("/api/docs/47")
        self.assertIn("<h1>", rendered["html"])
        self.assertEqual(rendered["number"], 47)
        with self.assertRaises(HTTPError) as caught:
            self.get("/api/docs/999")
        self.assertEqual(caught.exception.code, 404)
        caught.exception.close()


if __name__ == "__main__":
    unittest.main()
