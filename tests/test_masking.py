"""Tests for pipewarden.masking."""
import pytest
from pipewarden.masking import MaskingPolicy, MaskResult, mask_event_metadata, MASK


class TestMaskingPolicy:
    def test_defaults_contain_common_patterns(self):
        p = MaskingPolicy()
        assert p.is_sensitive("password")
        assert p.is_sensitive("api_key")
        assert p.is_sensitive("secret")
        assert p.is_sensitive("token")

    def test_non_sensitive_key(self):
        p = MaskingPolicy()
        assert not p.is_sensitive("row_count")
        assert not p.is_sensitive("pipeline")

    def test_case_insensitive(self):
        p = MaskingPolicy()
        assert p.is_sensitive("PASSWORD")
        assert p.is_sensitive("API_KEY")

    def test_custom_patterns(self):
        p = MaskingPolicy(patterns=[r"credit"])
        assert p.is_sensitive("credit_card")
        assert not p.is_sensitive("password")  # default not included

    def test_empty_mask_raises(self):
        with pytest.raises(ValueError):
            MaskingPolicy(mask="")

    def test_apply_masks_sensitive(self):
        p = MaskingPolicy()
        result = p.apply({"password": "s3cr3t", "user": "alice"})
        assert result["password"] == MASK
        assert result["user"] == "alice"

    def test_str(self):
        p = MaskingPolicy()
        assert "MaskingPolicy" in str(p)


class TestMaskResult:
    def test_str_contains_masked_keys(self):
        r = MaskResult(
            original_keys=["password", "user"],
            masked_keys=["password"],
            data={"password": MASK, "user": "alice"},
        )
        assert "password" in str(r)

    def test_str_contains_clean_keys(self):
        r = MaskResult(
            original_keys=["password", "user"],
            masked_keys=["password"],
            data={"password": MASK, "user": "alice"},
        )
        assert "user" in str(r)


class TestMaskEventMetadata:
    def test_default_policy_applied(self):
        data = {"token": "abc123", "pipeline": "etl"}
        result = mask_event_metadata(data)
        assert result.data["token"] == MASK
        assert result.data["pipeline"] == "etl"

    def test_masked_keys_listed(self):
        data = {"secret": "x", "count": 5}
        result = mask_event_metadata(data)
        assert "secret" in result.masked_keys
        assert "count" not in result.masked_keys

    def test_original_keys_preserved(self):
        data = {"a": 1, "b": 2}
        result = mask_event_metadata(data)
        assert set(result.original_keys) == {"a", "b"}

    def test_custom_policy(self):
        policy = MaskingPolicy(patterns=[r"credit"], mask="[REDACTED]")
        data = {"credit_card": "1234", "name": "bob"}
        result = mask_event_metadata(data, policy)
        assert result.data["credit_card"] == "[REDACTED]"
        assert result.data["name"] == "bob"

    def test_no_sensitive_keys(self):
        data = {"rows": 100, "pipeline": "load"}
        result = mask_event_metadata(data)
        assert result.masked_keys == []
