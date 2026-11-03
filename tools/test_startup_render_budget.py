"""An independent frame budget always restores before composition or failure."""
import unittest
from unittest.mock import Mock,patch
import startup_render_budget as module

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.memory=Mock();self.scope=Mock();self.scope.__enter__=Mock(return_value={'client.MaxFPS':0});self.scope.__exit__=Mock()
        self.budget=module.StartupRenderBudget()
        self.m=patch.object(module,'ResearchProcess',return_value=self.memory);self.m.start();self.addCleanup(self.m.stop)
        self.c=patch.object(module,'temporary_render_settings',return_value=self.scope);self.c.start();self.addCleanup(self.c.stop)

    def test_cap_is_restored_and_handle_closed(self):
        self.budget.start(7,{})
        self.budget.restore()
        self.scope.__exit__.assert_called_once_with(None,None,None);self.memory.close.assert_called_once()
        self.assertFalse(self.budget.active)

    def test_duplicate_start_does_not_create_another_owner(self):
        self.budget.start(7,{});self.budget.start(7,{})
        self.scope.__enter__.assert_called_once();self.budget.restore()

    def test_explicit_disable_never_writes(self):
        self.budget.start(7,{'startupRenderBudget':False})
        self.scope.__enter__.assert_not_called()

    def test_restore_failure_is_not_swallowed_and_handle_is_closed(self):
        self.budget.start(7,{});self.scope.__exit__.side_effect=ValueError('external setting conflict')
        with self.assertRaisesRegex(ValueError,'external'):self.budget.restore()
        self.memory.close.assert_called_once()

    def test_unsupported_metadata_preserves_normal_launch(self):
        self.scope.__enter__.side_effect=ValueError('Native quality value differs')
        self.budget.start(7,{})
        self.assertFalse(self.budget.active);self.memory.close.assert_called_once()

if __name__=='__main__':unittest.main()
