#!/usr/bin/env python
"""Test script to verify condense_content works with additional keys."""
import json
import unittest


class TestCondenseContent(unittest.TestCase):
    """Test cases for condense_content function"""

    def setUp(self):
        """Set up test data that will be used across multiple tests"""
        self.test_data = {
            "items": [
                {
                    "id": "deploy-123",
                    "name": "Deployment 1",
                    "taskId": "task-456",
                    "projectId": "proj-789",
                    "environmentId": "env-101",
                    "extraField": "should not appear",
                },
                {
                    "id": "deploy-124",
                    "name": "Deployment 2",
                    "taskId": "task-457",
                    "projectId": "proj-790",
                    "environmentId": "env-102",
                    "extraField": "should not appear",
                },
            ]
        }

    def condense_content_helper(self, additional_keys=None):
        """Helper method that mimics the condense_content function logic"""
        if additional_keys is None:
            additional_keys = []

        result = json.dumps(self.test_data)
        content_json = json.loads(result)
        normalized_items = [
            {k.casefold(): v for k, v in item.items()}
            for item in content_json.get("items", [])
        ]

        # Build condensed dict with id, name, and any additional keys
        condensed_json = []
        for item in normalized_items:
            condensed_item = {"id": item.get("id"), "name": item.get("name")}
            # Add any additional keys requested
            for key in additional_keys:
                key_lower = key.casefold()
                if key_lower in item:
                    condensed_item[key] = item.get(key_lower)
            condensed_json.append(condensed_item)

        return condensed_json

    def test_without_additional_keys(self):
        """Test condense_content without additional keys (only id and name)"""
        result = self.condense_content_helper()

        # Verify we have 2 items
        self.assertEqual(len(result), 2)

        # Verify first item has only id and name
        self.assertIn("id", result[0])
        self.assertIn("name", result[0])
        self.assertEqual(result[0]["id"], "deploy-123")
        self.assertEqual(result[0]["name"], "Deployment 1")

        # Verify additional fields are NOT present
        self.assertNotIn("taskId", result[0])
        self.assertNotIn("projectId", result[0])
        self.assertNotIn("environmentId", result[0])
        self.assertNotIn("extraField", result[0])

        # Verify we only have 2 keys
        self.assertEqual(len(result[0].keys()), 2)

    def test_with_all_additional_keys(self):
        """Test condense_content with multiple additional keys"""
        result = self.condense_content_helper(
            additional_keys=["taskId", "projectId", "environmentId"]
        )

        # Verify we have 2 items
        self.assertEqual(len(result), 2)

        # Verify first item has all requested fields
        self.assertIn("id", result[0])
        self.assertIn("name", result[0])
        self.assertIn("taskId", result[0])
        self.assertIn("projectId", result[0])
        self.assertIn("environmentId", result[0])

        # Verify values are correct
        self.assertEqual(result[0]["id"], "deploy-123")
        self.assertEqual(result[0]["name"], "Deployment 1")
        self.assertEqual(result[0]["taskId"], "task-456")
        self.assertEqual(result[0]["projectId"], "proj-789")
        self.assertEqual(result[0]["environmentId"], "env-101")

        # Verify extraField is NOT present
        self.assertNotIn("extraField", result[0])

        # Verify we have exactly 5 keys
        self.assertEqual(len(result[0].keys()), 5)

    def test_with_partial_additional_keys(self):
        """Test condense_content with only one additional key"""
        result = self.condense_content_helper(additional_keys=["taskId"])

        # Verify we have 2 items
        self.assertEqual(len(result), 2)

        # Verify first item has id, name, and taskId
        self.assertIn("id", result[0])
        self.assertIn("name", result[0])
        self.assertIn("taskId", result[0])
        self.assertEqual(result[0]["taskId"], "task-456")

        # Verify other additional fields are NOT present
        self.assertNotIn("projectId", result[0])
        self.assertNotIn("environmentId", result[0])
        self.assertNotIn("extraField", result[0])

        # Verify we have exactly 3 keys
        self.assertEqual(len(result[0].keys()), 3)

    def test_with_nonexistent_additional_key(self):
        """Test condense_content with a key that doesn't exist in the data"""
        result = self.condense_content_helper(additional_keys=["nonExistentKey"])

        # Verify we have 2 items
        self.assertEqual(len(result), 2)

        # Verify first item has only id and name (nonexistent key should be ignored)
        self.assertIn("id", result[0])
        self.assertIn("name", result[0])
        self.assertNotIn("nonExistentKey", result[0])

        # Verify we have exactly 2 keys
        self.assertEqual(len(result[0].keys()), 2)

    def test_case_insensitive_keys(self):
        """Test that key matching is case-insensitive"""
        # Test with different case variations
        result = self.condense_content_helper(additional_keys=["TASKID", "ProjectId"])

        # Verify the keys are found despite case differences
        self.assertIn("TASKID", result[0])
        self.assertIn("ProjectId", result[0])
        self.assertEqual(result[0]["TASKID"], "task-456")
        self.assertEqual(result[0]["ProjectId"], "proj-789")

    def test_second_item_values(self):
        """Test that both items are processed correctly"""
        result = self.condense_content_helper(additional_keys=["taskId"])

        # Verify second item
        self.assertEqual(result[1]["id"], "deploy-124")
        self.assertEqual(result[1]["name"], "Deployment 2")
        self.assertEqual(result[1]["taskId"], "task-457")


if __name__ == "__main__":
    unittest.main()
