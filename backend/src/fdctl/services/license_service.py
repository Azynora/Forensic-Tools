from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
try:
    import winreg  # type: ignore
except Exception:  # pragma: no cover - non-Windows fallback
    winreg = None  # type: ignore[assignment]

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from fdctl.paths import project_root
from fdctl.utils import ensure_dir, now_iso, read_json, write_json


PRODUCT_NAME = "FORENSICS_DISCORD"
OWNER_NAME = "Truong Trieu Vy"
OWNER_EMAIL = "trieuvy9198@gmail.com"
OWNER_MACHINE_FINGERPRINTS = {
    "[REDACTED_MACHINE_HASH]",
}
LICENSE_SCHEMA_VERSION = 3
INTEGRITY_MANIFEST_NAME = "BUILD_PROVENANCE.json"
ACTIVATION_FILE_NAME = "active_license.json"
REPORT_LICENSE_STATE_NAME = "license-state.js"
TRIAL_DAYS = 7
LEGACY_TRIAL_DAYS = 3
PRIVATE_KEY_ENV = "FDCTL_LICENSE_PRIVATE_KEY"
DEFAULT_LICENSE_STORAGE_ROOT = Path(r"D:\ForensicWorkspace")
LICENSE_HISTORY_NAME = "license_history.json"
COMPACT_LICENSE_MAGIC = b"FD"
COMPACT_LICENSE_SCHEMA_VERSION = 2
COMPACT_EMAIL_HASH_BYTES = 12
COMPACT_LICENSE_ID_BYTES = 8
COMPACT_MACHINE_HASH_BYTES = 12
TRIAL_REGISTRY_NAME = "trial_registry.json"
MAX_COMPACT_UNIX_TIMESTAMP = 0xFFFFFFFF
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEANa7zxA5/Kyv2+eMlGAvrqjUMo/9XAL79x6fQlN+g+Es=
-----END PUBLIC KEY-----
"""
LEGACY_PUBLIC_KEY_PEMS: tuple[str, ...] = (
    """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAXmobkVDnbDHV+zsnBKrzNNgdRiheFPs6aopag0GegII=
-----END PUBLIC KEY-----
""",
)

LICENSE_TYPES: dict[str, dict[str, Any]] = {
    "issued_7d": {
        "label": "Issued Access 7 Days",
        "defaultDays": 7,
        "features": ["cli", "report", "collection", "analysis", "autopsy"],
        "channel": "issued",
        "public": True,
    },
    "issued_30d": {
        "label": "Issued Access 30 Days",
        "defaultDays": 30,
        "features": ["cli", "report", "collection", "analysis", "autopsy"],
        "channel": "issued",
        "public": True,
    },
    "issued_365d": {
        "label": "Issued Access 365 Days",
        "defaultDays": 365,
        "features": ["cli", "report", "collection", "analysis", "autopsy"],
        "channel": "issued",
        "public": True,
    },
    "owner_unlimited": {
        "label": "Owner Unlimited Access",
        "defaultDays": 0,
        "features": ["cli", "report", "analysis", "autopsy", "owner"],
        "channel": "owner-issued",
        "public": False,
    },
}

LICENSE_TYPE_CODES = {
    "issued_7d": 1,
    "issued_30d": 2,
    "issued_365d": 4,
    "owner_unlimited": 9,
}
LICENSE_CODE_TYPES = {value: key for key, value in LICENSE_TYPE_CODES.items()}


def _source_checkout_present(root: Path | None = None) -> bool:
    base = root or project_root()
    return (
        (base / "backend" / "src" / "fdctl" / "cli.py").exists()
        and (base / "launch-analysis-terminal.cmd").exists()
    )


def _owner_machine_allowlist() -> set[str]:
    allowlist = {item.strip().lower() for item in OWNER_MACHINE_FINGERPRINTS if str(item).strip()}
    override = str(os.environ.get("FDCTL_OWNER_MACHINE_ALLOWLIST", "") or "").strip()
    if override:
        for item in override.replace(";", ",").split(","):
            normalized = item.strip().lower()
            if normalized:
                allowlist.add(normalized)
    return allowlist


def owner_source_bypass_allowed(root: Path | None = None) -> bool:
    forced = str(os.environ.get("FDCTL_OWNER_SOURCE_BYPASS", "") or "").strip().lower()
    if forced in {"1", "true", "yes", "on"}:
        return True
    if forced in {"0", "false", "no", "off"}:
        return False
    if getattr(sys, "frozen", False):
        return False
    if not _source_checkout_present(root):
        return False
    fingerprints = {machine_fingerprint().lower(), legacy_machine_fingerprint().lower()}
    return any(item in _owner_machine_allowlist() for item in fingerprints if item)


def license_enforcement_required(root: Path | None = None) -> bool:
    forced = str(os.environ.get("FDCTL_ENFORCE_LICENSE", "") or "").strip().lower()
    if forced in {"1", "true", "yes", "on"}:
        return True
    if forced in {"0", "false", "no", "off"}:
        return False
    if getattr(sys, "frozen", False):
        return True
    return not owner_source_bypass_allowed(root)


def license_issue_allowed(root: Path | None = None) -> bool:
    forced = str(os.environ.get("FDCTL_ALLOW_LICENSE_ISSUE", "") or "").strip().lower()
    if forced in {"1", "true", "yes", "on"}:
        return True
    return owner_source_bypass_allowed(root)


def support_root() -> Path:
    override = str(os.environ.get("FDCTL_LICENSE_HOME", "") or "").strip()
    if override:
        return ensure_dir(Path(override).expanduser().resolve())
    local_appdata = str(os.environ.get("LOCALAPPDATA", "") or "").strip()
    if local_appdata:
        return ensure_dir(Path(local_appdata) / PRODUCT_NAME)
    appdata = str(os.environ.get("APPDATA", "") or "").strip()
    if appdata:
        return ensure_dir(Path(appdata) / PRODUCT_NAME)
    return ensure_dir(project_root() / ".fdctl-license")


def issued_key_storage_root() -> Path:
    override = str(os.environ.get("FDCTL_ISSUED_KEY_HOME", "") or "").strip()
    if override:
        return ensure_dir(Path(override).expanduser().resolve())
    return ensure_dir(DEFAULT_LICENSE_STORAGE_ROOT)


def activation_path() -> Path:
    return ensure_dir(support_root() / "license") / ACTIVATION_FILE_NAME


def license_request_path() -> Path:
    return ensure_dir(support_root() / "license") / "license-request.txt"


def trial_registry_path() -> Path:
    return ensure_dir(support_root() / "license") / TRIAL_REGISTRY_NAME


def license_history_path() -> Path:
    return ensure_dir(support_root() / "license") / LICENSE_HISTORY_NAME


def _canonical_json(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _url_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _url_b64decode(data: str) -> bytes:
    padding = "=" * ((4 - (len(data) % 4)) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def ownership_sentinel() -> str:
    return hashlib.sha256(f"{OWNER_NAME}|{OWNER_EMAIL}|{PRODUCT_NAME}".encode("utf-8")).hexdigest()


def normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def canonicalize_gmail_address(value: str) -> str:
    normalized = normalize_email(value)
    if normalized.count("@") != 1:
        return normalized
    local_part, domain = normalized.split("@", 1)
    if domain != "gmail.com":
        return normalized
    local_part = local_part.split("+", 1)[0].replace(".", "")
    return f"{local_part}@gmail.com"


def validate_supported_email(value: str, field_name: str = "email") -> str:
    normalized = normalize_email(value)
    if not normalized or normalized.count("@") != 1 or not normalized.endswith("@gmail.com"):
        raise ValueError(f"{field_name} must be a valid Gmail address ending with @gmail.com.")
    canonical = canonicalize_gmail_address(normalized)
    local_part = canonical[:-10]
    if not local_part:
        raise ValueError(f"{field_name} must be a valid Gmail address ending with @gmail.com.")
    return canonical


def is_owner_email(email: str) -> bool:
    return normalize_email(email) == normalize_email(OWNER_EMAIL)


def email_fingerprint(value: str) -> bytes:
    normalized = validate_supported_email(value, "email")
    return hashlib.sha256(normalized.encode("utf-8")).digest()[:COMPACT_EMAIL_HASH_BYTES]


def machine_binding_hash(value: str) -> bytes:
    return hashlib.sha256(str(value or "").strip().lower().encode("utf-8")).digest()[:COMPACT_MACHINE_HASH_BYTES]


def current_machine_binding_hash() -> bytes:
    return machine_binding_hash(machine_fingerprint())


def current_machine_binding_hashes() -> set[str]:
    hashes = {machine_binding_hash(machine_fingerprint()).hex()}
    legacy = legacy_machine_fingerprint()
    if legacy:
        hashes.add(machine_binding_hash(legacy).hex())
    return hashes


def format_machine_name() -> str:
    return str(os.environ.get("COMPUTERNAME", "") or socket.gethostname()).strip() or socket.gethostname()


def normalized_license_key_letters(value: str) -> str:
    return _format_license_key_letters(value)


def machine_fingerprint() -> str:
    raw = "|".join(_machine_identity_components())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def legacy_machine_fingerprint() -> str:
    raw = "|".join(
        [
            socket.gethostname(),
            os.environ.get("COMPUTERNAME", ""),
            os.environ.get("USERNAME", ""),
            sys.platform,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _machine_guid() -> str:
    if sys.platform != "win32" or winreg is None:
        return ""
    candidates = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", "MachineGuid"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Cryptography", "MachineGuid"),
    ]
    for hive, subkey, value_name in candidates:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                text = str(value or "").strip().lower()
                if text:
                    return text
        except Exception:
            continue
    return ""


def _machine_identity_components() -> list[str]:
    machine_guid = _machine_guid()
    if machine_guid:
        return [
            machine_guid,
            str(os.environ.get("COMPUTERNAME", "") or socket.gethostname()).strip().lower(),
            sys.platform,
        ]
    return [
        socket.gethostname(),
        os.environ.get("COMPUTERNAME", ""),
        sys.platform,
    ]


def parse_timestamp(value: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def now_utc() -> datetime:
    return datetime.now(UTC)


def _default_profile(license_type: str) -> dict[str, Any]:
    if license_type not in LICENSE_TYPES:
        raise ValueError(f"Unsupported license type: {license_type}")
    return LICENSE_TYPES[license_type]


def license_types_summary(public_only: bool = True) -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": value["label"],
            "defaultDays": value["defaultDays"],
            "features": list(value["features"]),
            "channel": value["channel"],
        }
        for key, value in LICENSE_TYPES.items()
        if (not public_only) or bool(value.get("public", True))
    ]


def requested_license_types() -> list[str]:
    return [item["key"] for item in license_types_summary(public_only=True)]


def _public_keys() -> tuple[Ed25519PublicKey, ...]:
    pems = (PUBLIC_KEY_PEM, *LEGACY_PUBLIC_KEY_PEMS)
    return tuple(
        serialization.load_pem_public_key(pem.encode("utf-8"))  # type: ignore[misc]
        for pem in pems
    )  # type: ignore[return-value]


def _private_key_candidates() -> list[Path]:
    candidates: list[Path] = []
    override = str(os.environ.get(PRIVATE_KEY_ENV, "") or "").strip()
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.append(DEFAULT_LICENSE_STORAGE_ROOT / "forensics_license_private_key.pem")
    candidates.append(Path.home().resolve() / ".fdctl-secrets" / "foreinsics_license_private_key.pem")
    candidates.append(Path.home().resolve() / ".fdctl-secrets" / "forensics_license_private_key.pem")
    return candidates


def _private_key_path() -> Path:
    for path in _private_key_candidates():
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Private signing key not found. Set {PRIVATE_KEY_ENV} or place the key in %USERPROFILE%\\.fdctl-secrets."
    )


def _private_key() -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(_private_key_path().read_bytes(), password=None)  # type: ignore[return-value]


def _sign_bytes(data: bytes) -> str:
    signature = _private_key().sign(data)
    return _url_b64encode(signature)


def _verify_bytes(data: bytes, signature: str) -> None:
    _verify_with_any_public_key(_url_b64decode(signature), data)


def _verify_signature_bytes(data: bytes, signature: bytes) -> None:
    _verify_with_any_public_key(signature, data)


def _verify_with_any_public_key(signature: bytes, data: bytes) -> None:
    last_error: InvalidSignature | None = None
    for public_key in _public_keys():
        try:
            public_key.verify(signature, data)
            return
        except InvalidSignature as exc:
            last_error = exc
    raise ValueError("Signature is invalid.") from last_error


def _format_license_key_letters(raw_text: str) -> str:
    cleaned = "".join(ch for ch in str(raw_text or "").upper() if "A" <= ch <= "Z")
    if not cleaned:
        return ""
    return "-".join(cleaned[index:index + 4] for index in range(0, len(cleaned), 4))


def _letters_to_int(text: str) -> int:
    value = 0
    for ch in text:
        if ch < "A" or ch > "Z":
            raise ValueError("License key contains unsupported characters.")
        value = (value * 26) + (ord(ch) - ord("A"))
    return value


def _encode_letters_only(data: bytes) -> str:
    framed = b"\x01" + data
    number = int.from_bytes(framed, "big")
    letters: list[str] = []
    while number > 0:
        number, remainder = divmod(number, 26)
        letters.append(chr(ord("A") + remainder))
    return _format_license_key_letters("".join(reversed(letters or ["A"])))


def _decode_letters_only(text: str) -> bytes:
    compact = "".join(ch for ch in str(text or "").upper() if "A" <= ch <= "Z")
    if not compact:
        raise ValueError("License key format is invalid.")
    number = _letters_to_int(compact)
    raw = number.to_bytes(max(1, (number.bit_length() + 7) // 8), "big")
    if not raw or raw[0] != 0x01:
        raise ValueError("License key format is invalid.")
    return raw[1:]


def _masked_token_preview(token: str) -> str:
    formatted = _format_license_key_letters(token)
    if not formatted:
        return ""
    groups = [chunk for chunk in formatted.split("-") if chunk]
    if len(groups) <= 2:
        return formatted
    return "-".join([groups[0], groups[1], "****", groups[-1]])


def _load_license_history() -> dict[str, Any]:
    path = license_history_path()
    if not path.exists():
        return {
            "schemaVersion": 1,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "machineFingerprint": machine_fingerprint(),
            "machineName": format_machine_name(),
            "lastEmail": "",
            "entries": [],
        }
    try:
        data = read_json(path)
        if not isinstance(data, dict):
            raise ValueError("License history root is invalid.")
        entries = data.get("entries", [])
        if not isinstance(entries, list):
            entries = []
        data["entries"] = entries
        data["lastEmail"] = normalize_email(str(data.get("lastEmail", "") or ""))
        return data
    except Exception:
        return {
            "schemaVersion": 1,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "machineFingerprint": machine_fingerprint(),
            "machineName": format_machine_name(),
            "lastEmail": "",
            "entries": [],
        }


def _save_license_history(data: dict[str, Any]) -> None:
    data["schemaVersion"] = 1
    data["product"] = PRODUCT_NAME
    data["ownerName"] = OWNER_NAME
    data["ownerEmail"] = OWNER_EMAIL
    data["machineFingerprint"] = machine_fingerprint()
    data["machineName"] = format_machine_name()
    write_json(license_history_path(), data)


def remember_email_usage(
    email: str,
    *,
    license_type: str,
    license_label: str,
    token: str = "",
    source: str,
    expires_at: str = "",
    event: str,
) -> None:
    normalized_email = validate_supported_email(email, "email")
    history = _load_license_history()
    entries = list(history.get("entries", []) or [])
    entry = {
        "event": event,
        "email": normalized_email,
        "licenseType": str(license_type or ""),
        "licenseLabel": str(license_label or ""),
        "tokenPreview": _masked_token_preview(token),
        "source": str(source or ""),
        "machineFingerprint": machine_fingerprint(),
        "machineName": format_machine_name(),
        "expiresAt": str(expires_at or ""),
        "recordedAt": now_iso(),
    }
    entries.append(entry)
    history["entries"] = entries[-25:]
    history["lastEmail"] = normalized_email
    _save_license_history(history)


def last_used_email() -> str:
    history = _load_license_history()
    return normalize_email(str(history.get("lastEmail", "") or ""))


def license_usage_history(limit: int = 10) -> list[dict[str, Any]]:
    history = _load_license_history()
    entries = list(history.get("entries", []) or [])
    if limit <= 0:
        return entries
    return entries[-limit:]


def _pack_compact_license_payload(
    license_type: str,
    issued_at: datetime,
    expires_at: datetime,
    max_seats: int,
    license_id: bytes,
    email_hash: bytes,
    machine_hash: bytes,
) -> bytes:
    type_code = LICENSE_TYPE_CODES.get(license_type)
    if type_code is None:
        raise ValueError(f"Unsupported license type: {license_type}")
    if len(license_id) != COMPACT_LICENSE_ID_BYTES:
        raise ValueError("Compact license id length is invalid.")
    if len(email_hash) != COMPACT_EMAIL_HASH_BYTES:
        raise ValueError("Compact email hash length is invalid.")
    if len(machine_hash) != COMPACT_MACHINE_HASH_BYTES:
        raise ValueError("Compact machine hash length is invalid.")
    issued_seconds = int(issued_at.timestamp())
    expires_seconds = int(expires_at.timestamp())
    return b"".join(
        [
            COMPACT_LICENSE_MAGIC,
            bytes([COMPACT_LICENSE_SCHEMA_VERSION]),
            bytes([type_code]),
            issued_seconds.to_bytes(4, "big", signed=False),
            expires_seconds.to_bytes(4, "big", signed=False),
            bytes([max(1, min(255, int(max_seats)))]),
            license_id,
            email_hash,
            machine_hash,
        ]
    )


def _unpack_compact_license_payload(payload: bytes) -> dict[str, Any]:
    expected_length = 2 + 1 + 1 + 4 + 4 + 1 + COMPACT_LICENSE_ID_BYTES + COMPACT_EMAIL_HASH_BYTES + COMPACT_MACHINE_HASH_BYTES
    if len(payload) != expected_length:
        raise ValueError("Compact license payload length is invalid.")
    if payload[:2] != COMPACT_LICENSE_MAGIC:
        raise ValueError("Compact license magic is invalid.")
    schema_version = payload[2]
    if schema_version != COMPACT_LICENSE_SCHEMA_VERSION:
        raise ValueError("Compact license schema version is invalid.")
    type_code = payload[3]
    license_type = LICENSE_CODE_TYPES.get(type_code)
    if not license_type:
        raise ValueError("Compact license type code is invalid.")
    issued_seconds = int.from_bytes(payload[4:8], "big", signed=False)
    expires_seconds = int.from_bytes(payload[8:12], "big", signed=False)
    max_seats = payload[12]
    license_id_bytes = payload[13:13 + COMPACT_LICENSE_ID_BYTES]
    email_start = 13 + COMPACT_LICENSE_ID_BYTES
    email_hash = payload[email_start:email_start + COMPACT_EMAIL_HASH_BYTES]
    machine_hash = payload[email_start + COMPACT_EMAIL_HASH_BYTES:]
    issued_at = datetime.fromtimestamp(issued_seconds, UTC)
    expires_at = datetime.fromtimestamp(expires_seconds, UTC)
    return {
        "licenseType": license_type,
        "issuedAt": issued_at,
        "expiresAt": expires_at,
        "maxSeats": max_seats,
        "licenseId": license_id_bytes.hex(),
        "issuedToEmailHash": email_hash.hex(),
        "issuedToMachineHash": machine_hash.hex(),
    }


def _verify_legacy_license_token(token: str) -> dict[str, Any]:
    text = str(token or "").strip()
    if "." not in text:
        raise ValueError("License key format is invalid.")
    payload_part, signature_part = text.split(".", 1)
    payload_bytes = _url_b64decode(payload_part)
    payload = json.loads(payload_bytes.decode("utf-8"))
    _verify_bytes(payload_bytes, signature_part)
    if payload.get("product") != PRODUCT_NAME:
        raise ValueError("License key was not issued for this product.")
    if payload.get("ownershipSentinel") != ownership_sentinel():
        raise ValueError("License key owner metadata does not match this build.")
    not_before = parse_timestamp(str(payload.get("notBefore", "")))
    expires_at = parse_timestamp(str(payload.get("expiresAt", "")))
    current = now_utc()
    active = not_before <= current <= expires_at
    return {
        "active": active,
        "reason": "ok" if active else ("not-yet-valid" if current < not_before else "expired"),
        "payload": payload,
        "token": text,
        "displayToken": text,
        "expiresAt": expires_at.isoformat(),
        "notBefore": not_before.isoformat(),
        "secondsRemaining": max(0, int((expires_at - current).total_seconds())),
    }


def issue_license_key(
    issued_to_email: str,
    license_type: str,
    *,
    issued_by: str = OWNER_NAME,
    days_valid: int | None = None,
    max_seats: int = 1,
    features: list[str] | None = None,
    notes: str = "",
    release_channel: str = "bundle-release",
    bound_machine: str,
) -> dict[str, Any]:
    profile = _default_profile(license_type)
    normalized_email = validate_supported_email(issued_to_email, "issued_to_email")
    machine_fingerprint_text = str(bound_machine or "").strip().lower()
    if not machine_fingerprint_text:
        raise ValueError("bound_machine must be provided when issuing a license key.")
    days = int(days_valid if days_valid is not None else profile["defaultDays"])
    if days <= 0 and license_type != "owner_unlimited":
        raise ValueError("days_valid must be positive")
    issued_at = now_utc()
    if license_type == "owner_unlimited":
        expires_at = datetime.fromtimestamp(MAX_COMPACT_UNIX_TIMESTAMP, UTC)
        days = max(1, int((expires_at - issued_at).total_seconds() // 86400))
    else:
        expires_at = issued_at + timedelta(days=days)
    license_id_bytes = os.urandom(COMPACT_LICENSE_ID_BYTES)
    email_hash = email_fingerprint(normalized_email)
    machine_hash = machine_binding_hash(machine_fingerprint_text)
    compact_payload = _pack_compact_license_payload(
        license_type,
        issued_at,
        expires_at,
        max_seats,
        license_id_bytes,
        email_hash,
        machine_hash,
    )
    signature = _private_key().sign(compact_payload)
    token = _encode_letters_only(compact_payload + signature)
    payload = {
        "schemaVersion": LICENSE_SCHEMA_VERSION,
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "ownershipSentinel": ownership_sentinel(),
        "licenseId": license_id_bytes.hex(),
        "licenseType": license_type,
        "licenseLabel": profile["label"],
        "issuedToEmail": normalized_email,
        "issuedToName": "",
        "issuedBy": issued_by.strip() or OWNER_NAME,
        "issuedAt": issued_at.isoformat(),
        "notBefore": issued_at.isoformat(),
        "expiresAt": expires_at.isoformat(),
        "daysValid": days,
        "maxSeats": max(1, int(max_seats)),
        "features": list(features or profile["features"]),
        "releaseChannel": release_channel,
        "notes": notes.strip(),
        "issuedToEmailHash": email_hash.hex(),
        "issuedToMachineFingerprint": machine_fingerprint_text,
        "issuedToMachineHash": machine_hash.hex(),
        "compactKeyFormat": "letters-only",
    }
    return {"payload": payload, "token": token, "privateKeyPath": str(_private_key_path())}


def verify_license_token(token: str) -> dict[str, Any]:
    text = str(token or "").strip()
    if "." in text:
        return _verify_legacy_license_token(text)

    blob = _decode_letters_only(text)
    payload_length = 2 + 1 + 1 + 4 + 4 + 1 + COMPACT_LICENSE_ID_BYTES + COMPACT_EMAIL_HASH_BYTES + COMPACT_MACHINE_HASH_BYTES
    signature_length = 64
    if len(blob) != payload_length + signature_length:
        raise ValueError("License key format is invalid.")
    payload_bytes = blob[:payload_length]
    signature = blob[payload_length:]
    _verify_signature_bytes(payload_bytes, signature)
    unpacked = _unpack_compact_license_payload(payload_bytes)
    profile = _default_profile(str(unpacked["licenseType"]))
    not_before = unpacked["issuedAt"]
    expires_at = unpacked["expiresAt"]
    current = now_utc()
    active = not_before <= current <= expires_at
    payload = {
        "schemaVersion": LICENSE_SCHEMA_VERSION,
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "ownershipSentinel": ownership_sentinel(),
        "licenseId": unpacked["licenseId"],
        "licenseType": unpacked["licenseType"],
        "licenseLabel": profile["label"],
        "issuedToEmail": "",
        "issuedToName": "",
        "issuedToEmailHash": unpacked["issuedToEmailHash"],
        "issuedToMachineHash": unpacked["issuedToMachineHash"],
        "issuedAt": not_before.isoformat(),
        "notBefore": not_before.isoformat(),
        "expiresAt": expires_at.isoformat(),
        "daysValid": max(1, int((expires_at - not_before).total_seconds() // 86400)),
        "maxSeats": unpacked["maxSeats"],
        "features": list(profile["features"]),
        "releaseChannel": profile["channel"],
        "notes": "",
        "compactKeyFormat": "letters-only",
    }
    return {
        "active": active,
        "reason": "ok" if active else ("not-yet-valid" if current < not_before else "expired"),
        "payload": payload,
        "token": _format_license_key_letters(text),
        "displayToken": _format_license_key_letters(text),
        "expiresAt": expires_at.isoformat(),
        "notBefore": not_before.isoformat(),
        "secondsRemaining": max(0, int((expires_at - current).total_seconds())),
    }


def _validated_activation_email(payload: dict[str, Any], activation_email: str) -> str:
    claimed_email = validate_supported_email(activation_email, "Activation email")
    issued_to_email = normalize_email(str(payload.get("issuedToEmail", "") or ""))
    issued_email_hash = str(payload.get("issuedToEmailHash", "") or "").strip().lower()
    if issued_to_email:
        if claimed_email != issued_to_email:
            raise ValueError("Activation email does not match the email encoded in this license key.")
        return claimed_email
    if issued_email_hash:
        if email_fingerprint(claimed_email).hex() != issued_email_hash:
            raise ValueError("Activation email does not match the email encoded in this license key.")
        return claimed_email
    raise ValueError("License key does not contain an issued email identity.")
    return claimed_email


def activate_license_token(token: str, activation_email: str) -> dict[str, Any]:
    claimed_email = validate_supported_email(activation_email, "Activation email")
    verification = verify_license_token(token)
    if not verification.get("active"):
        raise ValueError("License key is not active or has expired.")
    payload = verification.get("payload", {}) if isinstance(verification.get("payload"), dict) else {}
    claimed_email = _validated_activation_email(payload, claimed_email)
    expected_machine_hash = str(payload.get("issuedToMachineHash", "") or "").strip().lower()
    current_machine_hashes = current_machine_binding_hashes()
    if expected_machine_hash and expected_machine_hash not in current_machine_hashes:
        raise ValueError("This license key was not issued for the current device.")
    activation_record = {
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "ownershipSentinel": ownership_sentinel(),
        "token": verification["token"],
        "activatedAt": now_iso(),
        "activatedForEmail": claimed_email,
        "machineFingerprint": machine_fingerprint(),
        "machineName": format_machine_name(),
        "issuedToMachineHash": expected_machine_hash,
    }
    write_json(activation_path(), activation_record)
    remember_email_usage(
        claimed_email,
        license_type=str(payload.get("licenseType", "")),
        license_label=str(payload.get("licenseLabel", "")),
        token=str(verification.get("token", "")),
        source="license-activation",
        expires_at=str(payload.get("expiresAt", "")),
        event="activate",
    )
    return current_license_status(selected_email=claimed_email, force_enforced=True)


def deactivate_license() -> None:
    path = activation_path()
    if path.exists():
        path.unlink()


def _load_trial_registry() -> dict[str, Any]:
    path = trial_registry_path()
    if not path.exists():
        return {
            "schemaVersion": 1,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "machineFingerprint": machine_fingerprint(),
            "machineName": format_machine_name(),
            "entries": {},
            "trialEmail": "",
        }
    try:
        data = read_json(path)
        if not isinstance(data, dict):
            raise ValueError("Trial registry root is invalid.")
        entries = data.get("entries", {})
        if not isinstance(entries, dict):
            entries = {}
        data["entries"] = entries
        return data
    except Exception:
        return {
            "schemaVersion": 1,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "machineFingerprint": machine_fingerprint(),
            "machineName": format_machine_name(),
            "entries": {},
            "trialEmail": "",
        }


def _save_trial_registry(data: dict[str, Any]) -> None:
    data["schemaVersion"] = 1
    data["product"] = PRODUCT_NAME
    data["ownerName"] = OWNER_NAME
    data["ownerEmail"] = OWNER_EMAIL
    data["machineFingerprint"] = machine_fingerprint()
    data["machineName"] = format_machine_name()
    write_json(trial_registry_path(), data)


def _trial_registry_key(email: str) -> str:
    return normalize_email(email)


def _trial_record(email: str) -> dict[str, Any]:
    normalized_email = validate_supported_email(email, "email")
    registry = _load_trial_registry()
    entries = registry.setdefault("entries", {})
    entry = entries.get(_trial_registry_key(normalized_email))
    if isinstance(entry, dict):
        return entry
    trial_email = normalize_email(str(registry.get("trialEmail", "") or ""))
    if trial_email and trial_email != normalized_email:
        raise ValueError(f"This device already used its free trial with {trial_email}.")

    started = now_utc()
    expires = started + timedelta(days=TRIAL_DAYS)
    record = {
        "mode": "trial",
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "ownershipSentinel": ownership_sentinel(),
        "email": normalized_email,
        "emailHash": email_fingerprint(normalized_email).hex(),
        "activatedAt": started.isoformat(),
        "expiresAt": expires.isoformat(),
        "licenseType": "trial_7d_email",
        "licenseLabel": "Free Trial 7 Days / 1 Email",
        "daysValid": TRIAL_DAYS,
        "machineFingerprint": machine_fingerprint(),
        "machineName": format_machine_name(),
    }
    entries[_trial_registry_key(normalized_email)] = record
    registry["trialEmail"] = normalized_email
    _save_trial_registry(registry)
    return record


def set_current_email_trial(email: str) -> dict[str, Any]:
    record = _trial_record(email)
    active_record = {
        "mode": "trial",
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "ownershipSentinel": ownership_sentinel(),
        "email": normalize_email(email),
        "emailHash": record.get("emailHash", ""),
        "activatedAt": record.get("activatedAt", ""),
        "expiresAt": record.get("expiresAt", ""),
        "licenseType": str(record.get("licenseType", "trial_7d_email")),
        "licenseLabel": str(record.get("licenseLabel", "Free Trial 7 Days / 1 Email")),
        "daysValid": TRIAL_DAYS,
        "machineFingerprint": machine_fingerprint(),
        "machineName": format_machine_name(),
    }
    write_json(activation_path(), active_record)
    remember_email_usage(
        normalize_email(email),
        license_type=str(record.get("licenseType", "trial_7d_email")),
        license_label=str(record.get("licenseLabel", "Free Trial 7 Days / 1 Email")),
        source="trial",
        expires_at=str(record.get("expiresAt", "")),
        event="trial-start",
    )
    return active_record


def _migrate_legacy_trial_record(record: dict[str, Any], email: str) -> dict[str, Any]:
    normalized_email = validate_supported_email(email, "email")
    registry = _load_trial_registry()
    trial_email = normalize_email(str(registry.get("trialEmail", "") or ""))
    if trial_email and trial_email != normalized_email:
        raise ValueError(f"This device already used its free trial with {trial_email}.")
    entries = registry.setdefault("entries", {})
    activated_at = str(record.get("activatedAt", "") or now_iso())
    expires_at = str(record.get("expiresAt", "") or (now_utc() + timedelta(days=LEGACY_TRIAL_DAYS)).isoformat())
    migrated = {
        "mode": "trial",
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "ownershipSentinel": ownership_sentinel(),
        "email": normalized_email,
        "emailHash": email_fingerprint(normalized_email).hex(),
        "activatedAt": activated_at,
        "expiresAt": expires_at,
        "licenseType": "trial_3d_email",
        "licenseLabel": "Free Trial 3 Days / 1 Email",
        "daysValid": int(record.get("daysValid", LEGACY_TRIAL_DAYS) or LEGACY_TRIAL_DAYS),
        "machineFingerprint": machine_fingerprint(),
        "machineName": format_machine_name(),
    }
    entries[_trial_registry_key(normalized_email)] = migrated
    registry["trialEmail"] = normalized_email
    _save_trial_registry(registry)
    write_json(activation_path(), migrated)
    remember_email_usage(
        normalized_email,
        license_type="trial_3d_email",
        license_label="Free Trial 3 Days / 1 Email",
        source="legacy-trial-migration",
        expires_at=expires_at,
        event="trial-migrate",
    )
    return migrated


def activation_request_text() -> str:
    request = (
        f"Forensics Suite activation request{os.linesep}"
        f"Owner: {OWNER_NAME} <{OWNER_EMAIL}>{os.linesep}"
        f"Machine fingerprint: {machine_fingerprint()}{os.linesep}"
        f"Hostname: {socket.gethostname()}{os.linesep}"
        f"Requested at: {now_iso()}{os.linesep}"
        f"Requested license types: {' | '.join(requested_license_types())}{os.linesep}"
    )
    path = license_request_path()
    path.write_text(request, encoding="utf-8")
    return request


def _trial_status(record: dict[str, Any], selected_email: str) -> dict[str, Any]:
    normalized_email = normalize_email(selected_email)
    stored_email = normalize_email(str(record.get("email", "") or ""))
    expires_at = parse_timestamp(str(record.get("expiresAt", "") or ""))
    current = now_utc()
    if stored_email != normalized_email:
        return {
            "active": False,
            "reason": "trial-email-mismatch",
            "enforced": True,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "licenseLabel": str(record.get("licenseLabel", "")),
            "licenseType": str(record.get("licenseType", "")),
            "issuedToEmail": stored_email,
            "issuedToName": "",
            "expiresAt": str(record.get("expiresAt", "")),
            "daysValid": int(record.get("daysValid", TRIAL_DAYS) or TRIAL_DAYS),
            "activationPath": str(activation_path()),
            "requestPath": str(license_request_path()),
        }
    active = current <= expires_at
    return {
        "active": active,
        "reason": "ok" if active else "trial-expired",
        "enforced": True,
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "licenseLabel": str(record.get("licenseLabel", "Free Trial 7 Days / 1 Email")),
        "licenseType": str(record.get("licenseType", "trial_7d_email")),
        "issuedToEmail": stored_email or normalized_email,
        "issuedToName": "",
        "issuedAt": str(record.get("activatedAt", "")),
        "expiresAt": str(record.get("expiresAt", "")),
        "daysValid": int(record.get("daysValid", TRIAL_DAYS) or TRIAL_DAYS),
        "features": ["demo"],
        "releaseChannel": "trial",
        "activationPath": str(activation_path()),
        "requestPath": str(license_request_path()),
        "machineName": str(record.get("machineName", "") or format_machine_name()),
        "secondsRemaining": max(0, int((expires_at - current).total_seconds())),
    }


def current_license_status(root: Path | None = None, selected_email: str = "", force_enforced: bool = False) -> dict[str, Any]:
    enforced = force_enforced or license_enforcement_required(root)
    if not enforced:
        return {
            "active": True,
            "reason": "owner-source-bypass",
            "enforced": False,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "licenseLabel": "Owner Source Workspace",
            "licenseType": "owner_source",
            "features": ["cli", "report", "collection", "analysis", "autopsy", "owner"],
            "issuedToEmail": OWNER_EMAIL,
            "issuedToName": OWNER_NAME,
            "expiresAt": "",
            "machineName": format_machine_name(),
            "activationPath": str(activation_path()),
            "requestPath": str(license_request_path()),
        }

    path = activation_path()
    normalized_email = ""
    if str(selected_email or "").strip():
        try:
            normalized_email = validate_supported_email(selected_email, "email")
        except ValueError as exc:
            return {
                "active": False,
                "reason": f"invalid: {exc}",
                "enforced": True,
                "product": PRODUCT_NAME,
                "ownerName": OWNER_NAME,
                "ownerEmail": OWNER_EMAIL,
                "licenseLabel": "",
                "licenseType": "",
                "issuedToEmail": "",
                "issuedToName": "",
                "expiresAt": "",
                "activationPath": str(activation_path()),
                "requestPath": str(license_request_path()),
                "activatedForEmail": "",
            }
    if not path.exists():
        if not normalized_email:
            return {
                "active": False,
                "reason": "email-required",
                "enforced": True,
                "product": PRODUCT_NAME,
                "ownerName": OWNER_NAME,
                "ownerEmail": OWNER_EMAIL,
                "licenseLabel": "",
                "licenseType": "",
                "issuedToEmail": "",
                "issuedToName": "",
                "expiresAt": "",
                "activationPath": str(path),
                "requestPath": str(license_request_path()),
                "activatedForEmail": "",
            }
        try:
            return _trial_status(set_current_email_trial(normalized_email), normalized_email)
        except ValueError as exc:
            return {
                "active": False, "reason": f"invalid: {exc}", "enforced": True,
                "product": PRODUCT_NAME, "ownerName": OWNER_NAME, "ownerEmail": OWNER_EMAIL,
                "licenseLabel": "", "licenseType": "", "issuedToEmail": normalized_email,
                "expiresAt": "", "features": [], "activationPath": str(path),
                "requestPath": str(license_request_path()),
            }

    try:
        record = read_json(path)
        if record.get("ownershipSentinel") != ownership_sentinel():
            raise ValueError("Stored activation record does not belong to this owner.")
        if str(record.get("mode", "")) == "trial":
            record_email = normalize_email(str(record.get("email", "") or ""))
            if not record_email and normalized_email:
                record = _migrate_legacy_trial_record(record, normalized_email)
                record_email = normalize_email(str(record.get("email", "") or ""))
            effective_email = normalized_email or record_email
            if not effective_email:
                return {
                    "active": False,
                    "reason": "email-required",
                    "enforced": True,
                    "product": PRODUCT_NAME,
                    "ownerName": OWNER_NAME,
                    "ownerEmail": OWNER_EMAIL,
                    "licenseLabel": str(record.get("licenseLabel", "")),
                    "licenseType": str(record.get("licenseType", "")),
                    "issuedToEmail": "",
                    "issuedToName": "",
                    "expiresAt": str(record.get("expiresAt", "")),
                    "activationPath": str(path),
                    "requestPath": str(license_request_path()),
                    "activatedForEmail": "",
                }
            return _trial_status(record, effective_email)
        verified = verify_license_token(str(record.get("token", "")))
        payload = verified.get("payload", {})
        activated_for_email = normalize_email(str(record.get("activatedForEmail", "") or ""))
        issued_to_email = normalize_email(str(payload.get("issuedToEmail", "") or ""))
        expected_machine_hash = str(payload.get("issuedToMachineHash", "") or "").strip().lower()
        current_machine_hashes = current_machine_binding_hashes()
        if expected_machine_hash and expected_machine_hash not in current_machine_hashes:
            raise ValueError("The stored license is bound to a different device.")
        effective_email = normalized_email or activated_for_email or issued_to_email
        if normalized_email and effective_email and normalized_email != effective_email:
            return {
                "active": False,
                "reason": "activation-email-mismatch",
                "enforced": True,
                "product": PRODUCT_NAME,
                "ownerName": OWNER_NAME,
                "ownerEmail": OWNER_EMAIL,
                "licenseId": str(payload.get("licenseId", "")),
                "licenseLabel": str(payload.get("licenseLabel", "")),
                "licenseType": str(payload.get("licenseType", "")),
                "issuedToEmail": effective_email,
                "issuedToName": str(payload.get("issuedToName", "")),
                "issuedAt": str(payload.get("issuedAt", "")),
                "expiresAt": str(payload.get("expiresAt", "")),
                "daysValid": int(payload.get("daysValid", 0) or 0),
                "features": list(payload.get("features", []) or []),
                "releaseChannel": str(payload.get("releaseChannel", "")),
                "activationPath": str(path),
                "requestPath": str(license_request_path()),
                "activatedForEmail": activated_for_email or issued_to_email,
                "machineName": str(record.get("machineName", "") or format_machine_name()),
                "secondsRemaining": int(verified.get("secondsRemaining", 0) or 0),
            }
        if activated_for_email and issued_to_email and activated_for_email != issued_to_email:
            raise ValueError("Stored activation email does not match the issued email in this license key.")
        display_email = activated_for_email or issued_to_email
        return {
            "active": bool(verified.get("active")),
            "reason": str(verified.get("reason", "unknown")),
            "enforced": True,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "licenseId": str(payload.get("licenseId", "")),
            "licenseLabel": str(payload.get("licenseLabel", "")),
            "licenseType": str(payload.get("licenseType", "")),
            "issuedToEmail": display_email,
            "issuedToName": str(payload.get("issuedToName", "")),
            "issuedAt": str(payload.get("issuedAt", "")),
            "expiresAt": str(payload.get("expiresAt", "")),
            "daysValid": int(payload.get("daysValid", 0) or 0),
            "features": list(payload.get("features", []) or []),
            "releaseChannel": str(payload.get("releaseChannel", "")),
            "activationPath": str(path),
            "requestPath": str(license_request_path()),
            "activatedForEmail": activated_for_email or issued_to_email,
            "machineName": str(record.get("machineName", "") or format_machine_name()),
            "secondsRemaining": int(verified.get("secondsRemaining", 0) or 0),
        }
    except Exception as exc:
        return {
            "active": False,
            "reason": f"invalid: {exc}",
            "enforced": True,
            "product": PRODUCT_NAME,
            "ownerName": OWNER_NAME,
            "ownerEmail": OWNER_EMAIL,
            "licenseLabel": "",
            "licenseType": "",
            "issuedToEmail": "",
            "issuedToName": "",
            "expiresAt": "",
            "activationPath": str(path),
            "requestPath": str(license_request_path()),
            "activatedForEmail": "",
        }


def require_active_license(feature: str, root: Path | None = None, selected_email: str = "") -> dict[str, Any]:
    status = current_license_status(root, selected_email=selected_email)
    if not status.get("active"):
        request_hint = activation_request_text() if status.get("enforced") else ""
        raise PermissionError(
            f"License activation is required for {feature}. "
            f"Use a Gmail address and owner-issued signed key. Owner contact: {OWNER_NAME} <{OWNER_EMAIL}>. "
            f"Activation request saved at {status.get('requestPath', '')}. "
            f"{request_hint}"
        )
    normalized_feature = feature.lower()
    if any(word in normalized_feature for word in ("collect", "workflow", "case-create")):
        entitlement = "collection"
    elif "analy" in normalized_feature or "supplement" in normalized_feature:
        entitlement = "analysis"
    elif "report" in normalized_feature or "autopsy" in normalized_feature:
        entitlement = "report" if "report" in status.get("features", []) else "autopsy"
    else:
        entitlement = "cli"
    features = status.get("features", [])
    if status.get("enforced") and entitlement not in features and "owner" not in features:
        raise PermissionError("This license does not include the requested feature. Trial access is limited to the synthetic demo.")
    return status


def build_integrity_message(manifest: dict[str, Any]) -> bytes:
    owner = manifest.get("owner", {}) if isinstance(manifest.get("owner"), dict) else {}
    files = manifest.get("files", []) if isinstance(manifest.get("files"), list) else []
    header = [
        str(manifest.get("project", "")),
        str(owner.get("name", "")),
        str(owner.get("email", "")),
        str(manifest.get("bundleVersion", "")),
        str(len(files)),
    ]
    rows: list[str] = []
    for item in sorted(files, key=lambda row: str(row.get("path", "")).lower()):
        rows.append(f"{item.get('path', '')}|{item.get('sha256', '')}|{item.get('sizeBytes', 0)}")
    return "\n".join(header + rows).encode("utf-8")


def integrity_signature_for_manifest(manifest: dict[str, Any]) -> str:
    return _sign_bytes(build_integrity_message(manifest))


def verify_bundle_integrity(root: Path | None = None) -> dict[str, Any]:
    bundle_root = root or project_root()
    if not license_enforcement_required(bundle_root):
        return {"ok": True, "enforced": False, "reason": "owner-source-bypass", "manifestPath": str(bundle_root / INTEGRITY_MANIFEST_NAME)}

    manifest_path = bundle_root / INTEGRITY_MANIFEST_NAME
    if not manifest_path.exists():
        return {"ok": False, "enforced": True, "reason": "missing-manifest", "manifestPath": str(manifest_path)}

    try:
        manifest = read_json(manifest_path)
        owner = manifest.get("owner", {}) if isinstance(manifest.get("owner"), dict) else {}
        if owner.get("name") != OWNER_NAME or owner.get("email") != OWNER_EMAIL:
            return {"ok": False, "enforced": True, "reason": "owner-mismatch", "manifestPath": str(manifest_path)}
        files = manifest.get("files", []) if isinstance(manifest.get("files"), list) else []
        for item in files:
            relative = Path(str(item.get("path", "") or ""))
            candidate = bundle_root / relative
            if not candidate.exists():
                return {"ok": False, "enforced": True, "reason": f"missing-file:{relative}", "manifestPath": str(manifest_path)}
            actual_hash = hashlib.sha256(candidate.read_bytes()).hexdigest().lower()
            expected_hash = str(item.get("sha256", "") or "").lower()
            if actual_hash != expected_hash:
                return {"ok": False, "enforced": True, "reason": f"hash-mismatch:{relative}", "manifestPath": str(manifest_path)}
        signature = str(manifest.get("integritySignature", "") or "")
        if not signature:
            return {"ok": False, "enforced": True, "reason": "missing-integrity-signature", "manifestPath": str(manifest_path)}
        _verify_bytes(build_integrity_message(manifest), signature)
        return {"ok": True, "enforced": True, "reason": "ok", "manifestPath": str(manifest_path)}
    except Exception as exc:
        return {"ok": False, "enforced": True, "reason": f"manifest-error:{exc}", "manifestPath": str(manifest_path)}


def require_bundle_access(feature: str, root: Path | None = None, selected_email: str = "") -> dict[str, Any]:
    integrity = verify_bundle_integrity(root)
    if not integrity.get("ok"):
        raise PermissionError(
            f"Official bundle integrity check failed for {feature}: {integrity.get('reason')}. "
            "This build may have been modified or its copyright/integrity markers removed."
        )
    return require_active_license(feature, root, selected_email=selected_email)


def report_license_state(root: Path | None = None) -> dict[str, Any]:
    status = current_license_status(root)
    return {
        "product": PRODUCT_NAME,
        "ownerName": OWNER_NAME,
        "ownerEmail": OWNER_EMAIL,
        "active": bool(status.get("active")),
        "reason": str(status.get("reason", "")),
        "enforced": bool(status.get("enforced", False)),
        "licenseType": str(status.get("licenseType", "")),
        "licenseLabel": str(status.get("licenseLabel", "")),
        "issuedToEmail": str(status.get("issuedToEmail", "")),
        "issuedToName": str(status.get("issuedToName", "")),
        "activatedForEmail": str(status.get("activatedForEmail", "")),
        "machineName": str(status.get("machineName", "")),
        "expiresAt": str(status.get("expiresAt", "")),
        "requestPath": str(status.get("requestPath", "")),
    }
