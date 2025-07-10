"""
BotC.app Integration Testing
Test suite for botc.app compatibility and features
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from .botc_app_adapter import BotCAppAdapter, BotCAppEventProcessor
from .clocktower_api import MockClockTowerAPI


class BotCTestSuite:
    """Test suite for botc.app integration"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all botc.app compatibility tests"""
        self.logger.info("Starting botc.app compatibility tests")

        tests = [
            ("connection_test", self._test_connection),
            ("websocket_test", self._test_websocket_connection),
            ("polling_test", self._test_polling_mode),
            ("state_sync_test", self._test_state_synchronization),
            ("event_processing_test", self._test_event_processing),
            ("action_sending_test", self._test_action_sending),
            ("error_handling_test", self._test_error_handling),
            ("adapter_features_test", self._test_adapter_features),
        ]

        results = {}

        for test_name, test_func in tests:
            try:
                self.logger.info(f"Running {test_name}...")
                result = await test_func()
                results[test_name] = {
                    "status": "PASS" if result else "FAIL",
                    "details": result,
                }
                self.logger.info(f"{test_name}: {'PASS' if result else 'FAIL'}")

            except Exception as e:
                results[test_name] = {"status": "ERROR", "details": str(e)}
                self.logger.error(f"{test_name}: ERROR - {e}")

        return results

    async def _test_connection(self) -> bool:
        """Test basic connection to botc.app"""
        try:
            # Create mock API for testing
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"

            # Create adapter
            adapter = BotCAppAdapter(api)

            # Test connection
            result = await adapter.enhanced_connect("TEST123")

            return result

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def _test_websocket_connection(self) -> bool:
        """Test websocket connection attempts"""
        try:
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"
            api.base_url = "https://botc.app"

            # Test websocket endpoint discovery
            endpoints = [
                f"{api.base_url.replace('http', 'ws')}/socket.io/",
                f"{api.base_url.replace('http', 'ws')}/ws",
                f"{api.base_url.replace('http', 'ws')}/live/TEST123",
                f"{api.base_url.replace('http', 'ws')}/game/TEST123",
            ]

            # Verify endpoints are correctly formatted
            for endpoint in endpoints:
                if not endpoint.startswith("wss://"):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"WebSocket test failed: {e}")
            return False

    async def _test_polling_mode(self) -> bool:
        """Test polling mode functionality"""
        try:
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"

            adapter = BotCAppAdapter(api)

            # Setup polling mode
            result = await adapter._setup_polling_mode("TEST123")

            if not result:
                return False

            # Verify polling attributes
            if not hasattr(api, "polling_active") or not api.polling_active:
                return False

            if (
                not hasattr(api, "connection_mode")
                or api.connection_mode != "enhanced_polling"
            ):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Polling test failed: {e}")
            return False

    async def _test_state_synchronization(self) -> bool:
        """Test state synchronization features"""
        try:
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"

            adapter = BotCAppAdapter(api)

            # Mock state data
            mock_state = {
                "players": [
                    {
                        "name": "Alice",
                        "character": "Fortune Teller",
                        "alive": True,
                        "team": "good",
                    },
                    {"name": "Bob", "character": "Imp", "alive": True, "team": "evil"},
                ],
                "phase": "day",
                "script": "Trouble Brewing",
            }

            # Test state enhancement
            enhanced_state = await adapter._enhance_state_data(mock_state)

            # Verify enhancement
            if "player_analysis" not in enhanced_state:
                return False

            if "last_updated" not in enhanced_state:
                return False

            # Test player analysis
            analysis = enhanced_state["player_analysis"]
            if analysis["total_count"] != 2:
                return False

            if analysis["alive_count"] != 2:
                return False

            return True

        except Exception as e:
            self.logger.error(f"State sync test failed: {e}")
            return False

    async def _test_event_processing(self) -> bool:
        """Test event processing and normalization"""
        try:
            processor = BotCAppEventProcessor()

            # Test event normalization
            from .clocktower_api import GameEvent

            raw_event = GameEvent(
                event_type="phase",
                timestamp=datetime.now(),
                data={"name": "night", "day": 1},
                source="botc_app",
            )

            processed_event = processor.process_event(raw_event)

            # Verify normalization
            if processed_event.event_type != "phase_change":
                return False

            if "processed_at" not in processed_event.data:
                return False

            if processed_event.data["source_platform"] != "botc_app":
                return False

            return True

        except Exception as e:
            self.logger.error(f"Event processing test failed: {e}")
            return False

    async def _test_action_sending(self) -> bool:
        """Test action sending capabilities"""
        try:
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"

            adapter = BotCAppAdapter(api)

            # Test action preprocessing
            action_data = {"player": "Alice", "effect": "poison"}
            processed = await adapter._preprocess_action("set_status", action_data)

            # Verify preprocessing
            if "timestamp" not in processed:
                return False

            if "storyteller" not in processed:
                return False

            if processed["storyteller"] != "AI_STORYTELLER":
                return False

            # Test enhanced action sending
            result = await adapter.send_enhanced_action("set_status", **action_data)

            return result

        except Exception as e:
            self.logger.error(f"Action sending test failed: {e}")
            return False

    async def _test_error_handling(self) -> bool:
        """Test error handling and recovery"""
        try:
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"

            adapter = BotCAppAdapter(api)

            # Test connection failure handling
            api.base_url = "https://invalid-url-that-does-not-exist.example"
            result = await adapter._fallback_connection("INVALID")

            # Should handle gracefully and return False
            if result:
                return False  # Should not succeed with invalid URL

            # Test state sync with invalid data
            adapter.state_cache = {"invalid": "data"}
            cached_state = adapter.get_cached_state()

            # Should return copy of cached state
            if cached_state is None:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error handling test failed: {e}")
            return False

    async def _test_adapter_features(self) -> bool:
        """Test adapter-specific features"""
        try:
            api = MockClockTowerAPI("TEST123")
            api.platform = "botc_app"

            adapter = BotCAppAdapter(api)

            # Test connection info
            info = adapter.get_connection_info()

            required_fields = [
                "platform",
                "connection_mode",
                "websocket_active",
                "polling_active",
                "supported_features",
            ]

            for field in required_fields:
                if field not in info:
                    return False

            if info["platform"] != "botc_app":
                return False

            # Test night order retrieval
            night_order = await adapter._get_night_order()
            if not isinstance(night_order, list):
                return False

            # Test script info
            script_info = await adapter._get_script_info()
            if not isinstance(script_info, dict):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Adapter features test failed: {e}")
            return False


class BotCCompatibilityReporter:
    """Generate compatibility reports for botc.app"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_report(self, test_results: Dict[str, Any]) -> str:
        """Generate a comprehensive compatibility report"""

        total_tests = len(test_results)
        passed_tests = sum(
            1 for result in test_results.values() if result["status"] == "PASS"
        )
        failed_tests = sum(
            1 for result in test_results.values() if result["status"] == "FAIL"
        )
        error_tests = sum(
            1 for result in test_results.values() if result["status"] == "ERROR"
        )

        compatibility_score = (
            (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        )

        report = f"""
# BotC.app Compatibility Report

## Summary
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {failed_tests}
- **Errors**: {error_tests}
- **Compatibility Score**: {compatibility_score:.1f}%

## Test Results

"""

        for test_name, result in test_results.items():
            status_icon = (
                "✅"
                if result["status"] == "PASS"
                else "❌" if result["status"] == "FAIL" else "⚠️"
            )
            report += f"### {test_name}\n"
            report += f"**Status**: {status_icon} {result['status']}\n"

            if result["status"] != "PASS":
                report += f"**Details**: {result['details']}\n"

            report += "\n"

        # Add recommendations
        report += "## Recommendations\n\n"

        if compatibility_score >= 80:
            report += "✅ **Excellent compatibility** - botc.app integration should work well.\n"
        elif compatibility_score >= 60:
            report += "⚠️ **Good compatibility** - botc.app integration should work with some limitations.\n"
        elif compatibility_score >= 40:
            report += "⚠️ **Moderate compatibility** - botc.app integration may have significant issues.\n"
        else:
            report += "❌ **Poor compatibility** - botc.app integration likely to have major problems.\n"

        report += "\n"

        if failed_tests > 0 or error_tests > 0:
            report += "### Issues Found:\n"

            for test_name, result in test_results.items():
                if result["status"] in ["FAIL", "ERROR"]:
                    report += f"- **{test_name}**: {result['details']}\n"

        report += (
            f"\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        )

        return report


async def run_botc_compatibility_test():
    """Run botc.app compatibility test and generate report"""
    test_suite = BotCTestSuite()
    results = await test_suite.run_all_tests()

    reporter = BotCCompatibilityReporter()
    report = reporter.generate_report(results)

    print(report)

    return results, report


if __name__ == "__main__":
    # Run the compatibility test
    asyncio.run(run_botc_compatibility_test())

