import unittest

from intent_router import parse_groq_route, request_needs_tools


class IntentRoutingTests(unittest.TestCase):
    def test_english_push_request_routes_to_action(self):
        prompt = (
            "Switch to ACTION mode. Use your PUSH tools to inspect the current "
            "Windows environment, list files, check Python and Git versions, "
            "and print the current date and time."
        )
        self.assertTrue(request_needs_tools(prompt))

    def test_english_directory_inspection_routes_to_action(self):
        self.assertTrue(request_needs_tools("List files in the current working directory."))

    def test_english_command_execution_routes_to_action(self):
        self.assertTrue(request_needs_tools("Run this PowerShell command on my computer."))

    def test_turkish_file_listing_still_routes_to_action(self):
        self.assertTrue(request_needs_tools("Masaüstündeki dosyaları listele."))

    def test_normal_greeting_stays_in_chat(self):
        self.assertFalse(request_needs_tools("Hello ManoMINI! How are you today?"))

    def test_explanation_request_stays_in_chat(self):
        self.assertFalse(request_needs_tools("Explain how API requests work in Python."))

    def test_parse_plain_groq_routes(self):
        self.assertEqual(parse_groq_route("ACTION"), "action")
        self.assertEqual(parse_groq_route("CHAT"), "chat")

    def test_parse_legacy_json_route(self):
        self.assertEqual(parse_groq_route('{"route":"action"}'), "action")

    def test_reject_invalid_groq_route(self):
        with self.assertRaises(ValueError):
            parse_groq_route("I think the user wants to do something.")


if __name__ == "__main__":
    unittest.main()
