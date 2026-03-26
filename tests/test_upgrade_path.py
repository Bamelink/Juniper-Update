import pytest
from lib.upgrade_path import compute_upgrade_path, parse_version, UpgradePathError


class TestParseVersion:
    def test_parse_valid_version(self):
        assert parse_version("21.3") == (21, 3)
        assert parse_version("23.4") == (23, 4)
        assert parse_version("23.4.1") == (23, 4)  # Extra minor versions ignored
    
    def test_parse_invalid_version(self):
        with pytest.raises(UpgradePathError):
            parse_version("invalid")
        with pytest.raises(UpgradePathError):
            parse_version("21")


class TestComputeUpgradePath:
    def test_path_21_3_to_23_4(self):
        """Test the example from requirements: 21.3 -> 23.4"""
        result = compute_upgrade_path("21.3", "23.4")
        assert result == ["21.4", "22.4", "23.4"]
    
    def test_path_same_version(self):
        """No steps needed if already at target"""
        result = compute_upgrade_path("23.4", "23.4")
        assert result == []
    
    def test_path_within_major_release(self):
        """Upgrade within same major release"""
        result = compute_upgrade_path("21.3", "21.4")
        assert result == ["21.4"]
    
    def test_path_already_on_4_train(self):
        """Already on .4 train"""
        result = compute_upgrade_path("21.4", "23.4")
        assert result == ["22.4", "23.4"]
    
    def test_downgrade_rejected(self):
        """Downgrade should raise error"""
        with pytest.raises(UpgradePathError):
            compute_upgrade_path("23.4", "21.3")
    
    def test_path_multiple_major_releases(self):
        """Jump across multiple major releases"""
        result = compute_upgrade_path("20.1", "23.2")
        assert result == ["20.4", "21.4", "22.4", "23.2"]
