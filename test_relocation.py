import unittest
from copy import deepcopy

from n8n_relocation_plan import apply_plan, plan


class RelocationTest(unittest.TestCase):
    def sample(self):
        w = {
            "name": "Invented order flow",
            "active": True,
            "nodes": [
                {
                    "id": "fetch",
                    "name": "Fetch",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {"url": "https://example.invalid"},
                    "credentials": {
                        "httpHeaderAuth": {"id": "old", "name": "Warehouse"}
                    },
                },
                {
                    "id": "child",
                    "name": "Child",
                    "type": "n8n-nodes-base.executeWorkflow",
                    "parameters": {
                        "workflowId": {"__rl": True, "value": "old-child", "mode": "id"}
                    },
                },
            ],
            "connections": {
                "Fetch": {"main": [[{"node": "Child", "type": "main", "index": 0}]]}
            },
        }
        c = {
            "credentials": [
                {"id": "new", "name": "Warehouse", "type": "httpHeaderAuth"}
            ],
            "workflows": {"old-child": "new-child"},
        }
        return w, c

    def test_complete_plan_and_only_allowed_fields_change(self):
        w, c = self.sample()
        before = deepcopy(w)
        p = plan(w, c)
        r = apply_plan(w, c, p)
        self.assertTrue(p["ready"])
        self.assertEqual(w, before)
        self.assertFalse(r["active"])
        self.assertEqual(r["nodes"][0]["credentials"]["httpHeaderAuth"]["id"], "new")
        self.assertEqual(
            r["nodes"][1]["parameters"]["workflowId"]["value"], "new-child"
        )
        self.assertEqual(r["connections"], w["connections"])
        self.assertEqual(r["nodes"][0]["parameters"], w["nodes"][0]["parameters"])

    def test_ambiguous_names_fail_closed(self):
        w, c = self.sample()
        c["credentials"].append(
            {"id": "other", "name": "Warehouse", "type": "httpHeaderAuth"}
        )
        p = plan(w, c)
        self.assertFalse(p["ready"])
        with self.assertRaises(ValueError):
            apply_plan(w, c, p)

    def test_explicit_typed_mapping_resolves_ambiguity(self):
        w, c = self.sample()
        c["credentials"].append(
            {"id": "other", "name": "Warehouse", "type": "httpHeaderAuth"}
        )
        c["explicit_credentials"] = {"httpHeaderAuth:old": "other"}
        self.assertEqual(
            apply_plan(w, c, plan(w, c))["nodes"][0]["credentials"]["httpHeaderAuth"][
                "id"
            ],
            "other",
        )

    def test_wrong_credential_type_does_not_match(self):
        w, c = self.sample()
        c["credentials"][0]["type"] = "oauth2Api"
        self.assertFalse(plan(w, c)["ready"])

    def test_dynamic_workflow_expression_is_unresolved(self):
        w, c = self.sample()
        w["nodes"][1]["parameters"]["workflowId"]["value"] = "={{ $json.id }}"
        self.assertFalse(plan(w, c)["ready"])

    def test_stale_or_tampered_plan_is_rejected(self):
        w, c = self.sample()
        p = plan(w, c)
        w["name"] = "edited"
        with self.assertRaises(ValueError):
            apply_plan(w, c, p)
        w, c = self.sample()
        p = plan(w, c)
        p["operations"][0]["after"]["id"] = "injected"
        with self.assertRaises(ValueError):
            apply_plan(w, c, p)

    def test_catalog_never_accepts_credential_payloads(self):
        w, c = self.sample()
        c["credentials"][0]["data"] = {"token": "invented"}
        with self.assertRaises(ValueError):
            plan(w, c)

    def test_duplicate_node_ids_reject(self):
        w, c = self.sample()
        w["nodes"][1]["id"] = "fetch"
        with self.assertRaises(ValueError):
            plan(w, c)


if __name__ == "__main__":
    unittest.main()
