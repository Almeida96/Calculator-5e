import asyncio
import importlib.util
import sys
import unittest

HAS_MCP = importlib.util.find_spec("mcp") is not None


@unittest.skipUnless(HAS_MCP, "Install .[mcp] for the protocol integration test")
class McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_discovery_calculation_comparison_and_validation(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async with asyncio.timeout(30):
            params = StdioServerParameters(
                command=sys.executable, args=["-m", "calculator_5e", "mcp"]
            )
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                    self.assertEqual(
                        {tool.name for tool in tools},
                        {"plan_journey", "compare_paces", "travel_rules"},
                    )
                    self.assertTrue(all(tool.annotations.readOnlyHint for tool in tools))
                    route = {
                        "legs": [{"name": "Road", "distance": 38}],
                        "pace": "fast",
                        "hours_per_day": 10,
                    }
                    result = await session.call_tool("plan_journey", {"journey": route})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.structuredContent["moving_hours"], 10)
                    self.assertEqual(
                        result.structuredContent["days"][0]["forced_march_saves"][-1],
                        {"after_hour": 10, "dc": 12},
                    )
                    compared = await session.call_tool("compare_paces", {"journey": route})
                    self.assertFalse(compared.isError)
                    self.assertLess(
                        compared.structuredContent["paces"]["fast"]["moving_hours"],
                        compared.structuredContent["paces"]["slow"]["moving_hours"],
                    )
                    rules = await session.call_tool("travel_rules", {})
                    self.assertFalse(rules.isError)
                    self.assertIn("2014", rules.structuredContent["edition"])
                    for invalid in (
                        {**route, "hours_per_day": 0},
                        {**route, "legs": [{"name": "Road", "distance": True}]},
                        {**route, "unexpected": 1},
                        {**route, "custom_speed": 5},
                    ):
                        error = await session.call_tool("plan_journey", {"journey": invalid})
                        self.assertTrue(error.isError)
                    recovery = await session.call_tool("plan_journey", {"journey": route})
                    self.assertFalse(recovery.isError)
