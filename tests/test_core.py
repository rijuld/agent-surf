# -*- coding: utf-8 -*-
"""Tests for AgentSurf core class."""

import pytest

from agent_surf.config import Config
from agent_surf.core import AgentSurf


@pytest.fixture
def eyes(tmp_path):
    config = Config(config_path=tmp_path / "config.yaml")
    return AgentSurf(config=config)


class TestAgentSurf:
    def test_init(self, eyes):
        assert eyes.config is not None

    def test_doctor(self, eyes):
        results = eyes.doctor()
        assert isinstance(results, dict)
        assert "web" in results
        assert "github" in results

    def test_doctor_report(self, eyes):
        report = eyes.doctor_report()
        assert isinstance(report, str)
        assert "Agent Surf" in report
