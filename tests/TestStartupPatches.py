import unittest

from src.patches.startup_patches import is_qt_mode


class TestStartupPatches(unittest.TestCase):
    def test_qt_mode(self):
        self.assertTrue(is_qt_mode({"gui": {"type": "qt"}}, []))

    def test_headless_is_not_qt_mode(self):
        config = {"gui": {"type": "qt"}}

        self.assertFalse(is_qt_mode(config, ["--headless"]))
        self.assertFalse(is_qt_mode(config, ["-h"]))

    def test_non_qt_ui_is_not_qt_mode(self):
        self.assertFalse(is_qt_mode({"gui": {"type": "web"}}, []))
        self.assertFalse(is_qt_mode({"use_gui": False}, []))


if __name__ == "__main__":
    unittest.main()
