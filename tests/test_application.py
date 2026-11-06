"""Offline tests: real SDK message types, simulated streams, no Claude calls."""
import asyncio
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from verify_data import verify_order, verify_sales
from claude_agent_sdk import (
    AssistantMessage, ResultMessage, ToolResultBlock, ToolUseBlock, UserMessage,
)


def result(**overrides):
    fields = dict(subtype="success", duration_ms=10, duration_api_ms=10,
                  is_error=False, num_turns=2, session_id="offline-test",
                  result="The operations team owns escalations. [policy.txt, Section 3]")
    fields.update(overrides)
    return ResultMessage(**fields)


async def stream(messages):
    for message in messages:
        yield message


class AgentLoopTests(unittest.TestCase):
    def setUp(self):
        self.target = app.resolve_target("policy.txt", "ask")

    def read_messages(self, *, path=None, error=False, result_id="read-1"):
        return [
            AssistantMessage(model="offline-test", content=[
                ToolUseBlock(id="read-1", name="Read", input={"file_path": str(path or self.target)})]),
            UserMessage(content=[ToolResultBlock(tool_use_id=result_id,
                                                content="Section 3: operations team", is_error=error)]),
        ]

    def collect(self, messages):
        with redirect_stderr(io.StringIO()):
            return asyncio.run(app.collect_report(stream(messages), self.target))

    def test_successful_read_and_final_report(self):
        final = result()
        self.assertEqual(self.collect(self.read_messages()+[final]), final.result)

    def test_relative_tool_path_matches_target(self):
        self.assertIn("operations", self.collect(self.read_messages(path="policy.txt")+[result()]))

    def test_turn_limit_is_failure_even_if_partial_text_exists(self):
        with self.assertRaisesRegex(RuntimeError, "error_max_turns"):
            self.collect(self.read_messages()+[result(subtype="error_max_turns")])

    def test_error_flag_is_failure_even_when_subtype_says_success(self):
        with self.assertRaisesRegex(RuntimeError, "did not complete"):
            self.collect(self.read_messages()+[result(is_error=True)])

    def test_failed_read_does_not_count_as_evidence(self):
        with self.assertRaisesRegex(RuntimeError, "No successful Read"):
            self.collect(self.read_messages(error=True)+[result()])

    def test_mismatched_tool_result_id_does_not_count(self):
        with self.assertRaisesRegex(RuntimeError, "No successful Read"):
            self.collect(self.read_messages(result_id="another-call")+[result()])

    def test_reading_other_file_does_not_count(self):
        with self.assertRaisesRegex(RuntimeError, "No successful Read"):
            self.collect(self.read_messages(path=app.PROJECT_DIR / "release_notes.txt")+[result()])

    def test_final_text_without_a_read_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "No successful Read"):
            self.collect([result()])

    def test_missing_final_message_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, "without a ResultMessage"):
            self.collect(self.read_messages())

    def test_empty_result_is_failure(self):
        for text in (None, "", "   "):
            with self.subTest(text=text), self.assertRaisesRegex(RuntimeError, "no final report"):
                self.collect(self.read_messages()+[result(result=text)])

    def test_plain_user_message_is_not_treated_as_tool_feedback(self):
        with self.assertRaisesRegex(RuntimeError, "No successful Read"):
            self.collect([UserMessage(content="hello"), result()])


class ApplicationTests(unittest.TestCase):
    def test_read_only_sdk_configuration(self):
        options = app.make_options(5, None)
        self.assertEqual(options.tools, ["Read"])
        self.assertEqual(options.allowed_tools, ["Read"])
        self.assertEqual(options.setting_sources, [])
        self.assertTrue(options.strict_mcp_config)
        self.assertEqual(options.mcp_servers, {})

    def test_target_validation(self):
        for filename, mode in [("../requirements.txt","summarize"),
                               ("missing.txt","summarize"),("policy.txt","data")]:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                app.resolve_target(filename, mode)

    def test_all_modes_have_offline_prompt_previews(self):
        for mode in app.DEFAULT_FILES:
            args=[mode,"--dry-run"]
            if mode=="ask":
                args += ["--question","Who owns escalations?"]
            with self.subTest(mode=mode), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(app.main(args),0)
                self.assertIn("Use Read",output.getvalue())

    def test_question_is_required_for_ask(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            app.main(["ask","--dry-run"])
        self.assertEqual(raised.exception.code,2)

    def test_sample_totals_and_null_are_verified_independently(self):
        sales=verify_sales(app.PROJECT_DIR / "sales.csv")
        order=verify_order(app.PROJECT_DIR / "order.json")
        self.assertEqual(sales["data_rows"],3)
        self.assertEqual(sales["units_by_item"],{"Notebook":3,"Pen":3})
        self.assertIsNone(order["total"])
        self.assertTrue(order["total_is_null"])

    def test_invalid_csv_units_are_reported(self):
        with patch.object(Path,"open",return_value=io.StringIO("item,units\nNotebook,unknown\n")):
            with self.assertRaisesRegex(ValueError,"line 2"):
                verify_sales(Path("sales.csv"))

    def test_missing_json_total_is_not_silently_replaced_with_null(self):
        with patch.object(Path,"read_text",return_value='{"order_id":42,"status":"pending"}'):
            with self.assertRaisesRegex(ValueError,"Missing order field: total"):
                verify_order(Path("order.json"))


if __name__=="__main__":
    unittest.main()
