"""Tests for src.utils.version.Version."""

from src.utils.version import Version


class TestVersionParsing:
    def test_simple_version(self):
        v = Version("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.is_prerelease is False

    def test_two_part(self):
        v = Version("1.2")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 0

    def test_single_part(self):
        v = Version("5")
        assert v.major == 5
        assert v.minor == 0
        assert v.patch == 0

    def test_prerelease_alpha(self):
        v = Version("1.0.0a1")
        assert v.is_prerelease is True
        assert v.prerelease_type == "a"
        assert v.prerelease_number == 1

    def test_prerelease_beta(self):
        v = Version("2.0.0b3")
        assert v.is_prerelease is True
        assert v.prerelease_type == "b"
        assert v.prerelease_number == 3

    def test_prerelease_rc(self):
        v = Version("1.0.0rc2")
        assert v.is_prerelease is True
        assert v.prerelease_type == "rc"
        assert v.prerelease_number == 2

    def test_prerelease_dev(self):
        v = Version("0.1.0dev")
        assert v.is_prerelease is True
        assert v.prerelease_type == "dev"
        assert v.prerelease_number == 0

    def test_whitespace_stripped(self):
        v = Version("  1.2.3  ")
        assert v.major == 1

    def test_additional_parts(self):
        v = Version("1.2.3.4")
        assert v.additional == [4]

    def test_repr(self):
        v = Version("1.0.0")
        assert repr(v) == "Version('1.0.0')"

    def test_str(self):
        v = Version("1.0.0")
        assert str(v) == "1.0.0"


class TestVersionComparison:
    def test_equal(self):
        assert Version("1.0.0") == Version("1.0.0")

    def test_not_equal(self):
        assert Version("1.0.0") != Version("2.0.0")

    def test_less_than_major(self):
        assert Version("1.0.0") < Version("2.0.0")

    def test_less_than_minor(self):
        assert Version("1.1.0") < Version("1.2.0")

    def test_less_than_patch(self):
        assert Version("1.0.1") < Version("1.0.2")

    def test_greater_than(self):
        assert Version("2.0.0") > Version("1.0.0")

    def test_le(self):
        assert Version("1.0.0") <= Version("1.0.0")
        assert Version("1.0.0") <= Version("2.0.0")

    def test_ge(self):
        assert Version("2.0.0") >= Version("2.0.0")
        assert Version("2.0.0") >= Version("1.0.0")

    def test_prerelease_less_than_release(self):
        assert Version("1.0.0a1") < Version("1.0.0")

    def test_alpha_less_than_beta(self):
        assert Version("1.0.0a1") < Version("1.0.0b1")

    def test_beta_less_than_rc(self):
        assert Version("1.0.0b1") < Version("1.0.0rc1")

    def test_dev_less_than_alpha(self):
        assert Version("1.0.0dev1") < Version("1.0.0a1")

    def test_prerelease_number_ordering(self):
        assert Version("1.0.0rc1") < Version("1.0.0rc2")

    def test_equal_prerelease(self):
        assert Version("1.0.0a1") == Version("1.0.0a1")
