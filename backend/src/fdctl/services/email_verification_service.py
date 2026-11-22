"""
Forensics Suite — Strict Email Verification & Anti-Abuse Service
Copyright (c) 2026 Truong Trieu Vy (trieuvy9198@gmail.com). All rights reserved.

Provides multi-layer validation for license issuance and client activations:
1. Syntax & RFC Compliance (length, structure, canonical normalization).
2. Disposable / Temporary / Trash Email Domain Blacklisting.
3. Domain DNS & MX Record Validation (Google, Microsoft, Corporate).
4. Active SMTP Mailbox Existence Probing (detects non-existent typed addresses).
5. Challenge-Response OTP Verification (guarantees mailbox ownership).
6. Complete Bilingual Localization (English & Vietnamese).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import smtplib
import socket
import subprocess
import sys
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 1. DISPOSABLE / TRASH EMAIL DOMAINS (Over 160 common throwaway domains)
# ---------------------------------------------------------------------------
DISPOSABLE_DOMAINS: frozenset[str] = frozenset({
    "10minutemail.com", "10minutemail.net", "10minutemail.org", "10mail.org",
    "temp-mail.org", "temp-mail.io", "tempmail.net", "tempmail.com", "tempmailaddress.com",
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.org", "guerrillamail.biz",
    "guerrillamailblock.com", "sharklasers.com", "grr.la", "pokemail.net", "spam4.me",
    "mailinator.com", "mailinater.com", "suremail.info", "zippymail.info",
    "yopmail.com", "yopmail.net", "yopmail.fr", "cool.fr.nf", "jetable.fr.nf",
    "dispostable.com", "trashmail.com", "trashmail.net", "trashmail.de", "trash-mail.com",
    "getairmail.com", "fakemailgenerator.com", "mohmal.com", "crazymailing.com",
    "generator.email", "emailondeck.com", "throwawaymail.com", "tempail.com",
    "mytemp.email", "mytempemail.com", "inboxkitten.com", "burnermail.io",
    "nada.ltd", "getnada.com", "dropmail.me", "tempinbox.com", "maildrop.cc",
    "discard.email", "spambog.com", "mailexpire.com", "mailnesia.com", "fakeinbox.com",
    "mailcatch.com", "harakirimail.com", "mintemail.com", "byom.de", "dayrep.com",
    "armyspy.com", "cuvox.de", "einrot.com", "fleckens.hu", "gustr.com",
    "jourrapide.com", "rhyta.com", "superrito.com", "teleworm.us", "mytempmail.com",
    "chacuo.net", "0815.ru", "0-mail.com", "0clickemail.com", "10minutemail.be",
    "20minutemail.com", "anonbox.net", "antichef.com", "antichef.net",
    "binkmail.com", "bobmail.info", "brefmail.com", "burntmail.com",
    "cachedot.net", "cashette.com", "centermail.com", "centermail.net",
    "chogmail.com", "crapmail.org", "deadaddress.com", "disposeamail.com",
    "disposableinbox.com", "drdrb.net", "dumpmail.de", "e4ward.com",
    "emailmiser.com", "emailthe.net", "eyepaste.com", "fastchemail.com",
    "filzmail.com", "getonemail.com", "gishpuppy.com", "gowikimail.com",
    "hidemail.de", "incognitomail.org", "kasmail.com", "koszmail.pl",
    "kurzepost.de", "lifebyfood.com", "link2mail.net", "lookugly.com",
    "lortemail.dk", "madfientist.com", "mail-temporaire.fr", "mailblocks.com",
    "mailcatch.com", "maildrop.cc", "maildu.de", "maileater.com",
    "mailhazard.com", "mailimate.com", "mailmoat.com", "mailnull.com",
    "mailslurp.com", "meltmail.com", "messagebeamer.de", "mytrashmail.com",
    "nobulk.com", "noclickemail.com", "nomail.xl.cx", "nospam.ze.tc",
    "nowmymail.com", "nurfuerspam.de", "oneoffmail.com", "pookmail.com",
    "privacy.net", "recursor.net", "safetymail.info", "sendspamhere.com",
    "shortmail.net", "skeefmail.com", "slopsbox.com", "sofort-mail.de",
    "sogetthis.com", "soodonims.com", "spambox.us", "spamfree24.org",
    "spamgourmet.com", "spamhole.com", "spaml.com", "spamex.com",
    "spamevader.com", "spamspot.com", "spamtrap.ro", "speed.1s.fr",
    "superstachel.de", "tagmail.com", "tafmail.com", "tempemail.net",
    "tempemail.co", "tempemail.net", "temporaryforwarding.com", "tempthe.net",
    "trashymail.com", "twinmail.de", "tyldd.com", "uggsrock.com",
    "upwardthought.com", "veryrealemail.com", "wegwerfadresse.de",
    "wegwerfmail.de", "wegwerfmail.net", "wegwerfmail.org", "whyspam.me",
    "willhackforfood.biz", "willselfdestruct.com", "wuzup.net", "wuzupmail.net",
    "zoemail.org", "zillamail.com",
})

# ---------------------------------------------------------------------------
# 2. PROVIDER PROFILES
# ---------------------------------------------------------------------------
GOOGLE_DOMAINS: frozenset[str] = frozenset({"gmail.com", "googlemail.com"})
MICROSOFT_DOMAINS: frozenset[str] = frozenset({
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "outlook.com.vn", "hotmail.com.vn", "live.com.vn",
    "outlook.fr", "outlook.de", "outlook.co.uk", "hotmail.co.uk",
})

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

# ---------------------------------------------------------------------------
# 3. BILINGUAL LOCALIZATION STRINGS (VI / EN)
# ---------------------------------------------------------------------------
MESSAGES: dict[str, dict[str, str]] = {
    "missing_at": {
        "vi": "{field} không hợp lệ (thiếu ký tự '@').",
        "en": "Invalid {field} format (missing '@' character).",
    },
    "too_long": {
        "vi": "{field} vượt quá độ dài tối đa 254 ký tự.",
        "en": "{field} exceeds maximum allowed length of 254 characters.",
    },
    "local_too_long": {
        "vi": "Phần tên người dùng (local-part) vượt quá 64 ký tự.",
        "en": "Email username (local-part) exceeds 64 characters limit.",
    },
    "invalid_rfc": {
        "vi": "{field} chứa ký tự không hợp lệ theo chuẩn RFC 5322.",
        "en": "{field} contains invalid characters according to RFC 5322 standard.",
    },
    "garbage_pattern": {
        "vi": "{field} mang dấu hiệu email ảo / gõ bừa ('{local}').",
        "en": "{field} contains obvious placeholder or random keystroke pattern ('{local}').",
    },
    "disposable_domain": {
        "vi": "Từ chối cấp phép: Tên miền '{domain}' là nhà cung cấp email rác / email tạm thời (Disposable Mail).",
        "en": "Licensing rejected: Domain '{domain}' is a known disposable/temporary email provider.",
    },
    "gmail_too_short": {
        "vi": "Email Google không hợp lệ: Tên người dùng Gmail '{local}' phải có từ 6 đến 30 ký tự.",
        "en": "Invalid Google email: Gmail username '{local}' must be between 6 and 30 characters.",
    },
    "gmail_too_long": {
        "vi": "Email Google không hợp lệ: Tên người dùng Gmail '{local}' vượt quá 30 ký tự.",
        "en": "Invalid Google email: Gmail username '{local}' exceeds Google 30-character limit.",
    },
    "microsoft_too_short": {
        "vi": "Email Microsoft '{email}' có tên người dùng quá ngắn.",
        "en": "Microsoft email '{email}' username is too short.",
    },
    "no_mx_server": {
        "vi": "Tên miền '{domain}' không có máy chủ Mail Server (MX Record). Email này không thể nhận thư và không tồn tại thực tế.",
        "en": "Domain '{domain}' has no active Mail Server (MX Record). This email cannot receive mail and does not exist.",
    },
    "google_mx_mismatch": {
        "vi": "Tên miền '{domain}' không trỏ về máy chủ thư chính thức của Google.",
        "en": "Domain '{domain}' MX records do not point to official Google mail servers.",
    },
    "ms_mx_mismatch": {
        "vi": "Tên miền '{domain}' không trỏ về máy chủ thư chính thức của Microsoft.",
        "en": "Domain '{domain}' MX records do not point to official Microsoft mail servers.",
    },
    "mailbox_not_found": {
        "vi": "Máy chủ thư của '{domain}' xác nhận: Hộp thư '{email}' KHÔNG TỒN TẠI (Error 550 / User unknown). Vui lòng kiểm tra lại, tránh gõ bừa địa chỉ email.",
        "en": "Mail server for '{domain}' confirms: Mailbox '{email}' DOES NOT EXIST (Error 550 / User unknown). Please provide a genuine address.",
    },
    "otp_invalid": {
        "vi": "Mã xác thực OTP không hợp lệ hoặc đã hết hạn. Yêu cầu cấp phép bị hủy.",
        "en": "Invalid or expired OTP verification code. License issuance cancelled.",
    },
    "otp_success": {
        "vi": "Xác thực quyền sở hữu hộp thư thành công qua mã OTP!",
        "en": "Mailbox ownership successfully verified via OTP challenge!",
    },
}


def _detect_system_language() -> str:
    """Detect configured language preference (vi or en) from settings, env or OS."""
    env_lang = os.environ.get("FDCTL_LANGUAGE", "").strip().lower()
    if env_lang in ("vi", "en"):
        return env_lang

    # Check settings.json
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = []
    if local_appdata:
        candidates.append(Path(local_appdata) / "FORENSIC_SUITE" / "settings.json")
        candidates.append(Path(local_appdata) / "FORENSICS_DISCORD" / "settings.json")
    candidates.append(Path.home() / ".config" / "FORENSIC_SUITE" / "settings.json")

    for p in candidates:
        if p.exists() and p.is_file():
            try:
                cfg = json.loads(p.read_text(encoding="utf-8"))
                val = str(cfg.get("language", "")).strip().lower()
                if val in ("vi", "en"):
                    return val
            except Exception:
                pass
    return "vi"


def _msg(key: str, lang: str | None = None, **kwargs: Any) -> str:
    chosen_lang = (lang or _detect_system_language()).lower()
    if chosen_lang not in ("vi", "en"):
        chosen_lang = "vi"
    tmpl = MESSAGES.get(key, {}).get(chosen_lang, MESSAGES.get(key, {}).get("en", key))
    return tmpl.format(**kwargs)


class EmailVerificationError(ValueError):
    """Raised when an email fails strict validation checks."""
    pass


class EmailVerificationService:
    """Enterprise-grade bilingual email verification engine for Forensics Suite licensing."""

    def __init__(self, secrets_dir: Path | None = None, language: str | None = None) -> None:
        self.secrets_dir = secrets_dir or (Path.home() / ".fdctl-secrets")
        self.otp_cache_file = self.secrets_dir / ".otp_cache.json"
        self.language = language or _detect_system_language()

    # -----------------------------------------------------------------------
    # Step 1: Syntax & Canonical Normalization
    # -----------------------------------------------------------------------
    @staticmethod
    def normalize_email(email: str) -> str:
        raw = str(email or "").strip()
        if not raw or "@" not in raw:
            return ""
        local_part, domain = raw.rsplit("@", 1)
        return f"{local_part.strip()}@{domain.strip().lower()}"

    @classmethod
    def canonicalize_email(cls, email: str) -> str:
        norm = cls.normalize_email(email)
        if not norm or "@" not in norm:
            return norm
        local_part, domain = norm.rsplit("@", 1)
        if domain in GOOGLE_DOMAINS:
            clean_local = local_part.split("+")[0].replace(".", "").lower()
            return f"{clean_local}@gmail.com"
        return norm

    # -----------------------------------------------------------------------
    # Step 2: Disposable / Throwaway Email Detection
    # -----------------------------------------------------------------------
    @classmethod
    def is_disposable_domain(cls, domain: str) -> bool:
        domain_lower = domain.strip().lower()
        if domain_lower in DISPOSABLE_DOMAINS:
            return True
        parts = domain_lower.split(".")
        if len(parts) > 2:
            root_domain = ".".join(parts[-2:])
            if root_domain in DISPOSABLE_DOMAINS:
                return True
        return False

    # -----------------------------------------------------------------------
    # Step 3: DNS MX (Mail Exchange) Resolution
    # -----------------------------------------------------------------------
    @staticmethod
    def query_mx_records(domain: str, timeout_seconds: float = 4.0) -> list[str]:
        domain_clean = domain.strip().lower()
        if not domain_clean or "." not in domain_clean:
            return []

        try:
            cmd = ["nslookup", "-type=MX", domain_clean]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            output = proc.stdout or ""
            matches = re.findall(r"mail exchanger\s*=\s*([a-zA-Z0-9\.\-]+)", output, re.IGNORECASE)
            cleaned = [m.strip().rstrip(".").lower() for m in matches if m.strip()]
            return list(dict.fromkeys(cleaned))
        except (subprocess.TimeoutExpired, Exception):
            pass

        try:
            ip = socket.gethostbyname(domain_clean)
            if ip and not ip.startswith("127."):
                return [domain_clean]
        except Exception:
            pass

        return []

    # -----------------------------------------------------------------------
    # Step 4: Strict Provider Rules (Google, Microsoft, Corporate)
    # -----------------------------------------------------------------------
    @classmethod
    def validate_strict_email(
        cls,
        email: str,
        *,
        field_name: str = "Email",
        check_mx: bool = True,
        probe_smtp: bool = True,
        lang: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform rigorous multi-layer verification on an email address with full i18n support:
        1. Format & length checking.
        2. Reject disposable / trash mail domains.
        3. Enforce Google personal rules (length 6-30 chars, MX must point to Google).
        4. Enforce Microsoft personal rules (MX must point to Microsoft).
        5. Enforce Corporate domain rules (must have valid, active MX mail servers).
        6. Optional active SMTP probe (detect non-existent typed addresses).
        """
        active_lang = lang or _detect_system_language()
        norm = cls.normalize_email(email)
        if not norm or "@" not in norm:
            raise EmailVerificationError(_msg("missing_at", active_lang, field=field_name))

        local_part, domain = norm.rsplit("@", 1)

        # 1. Basic RFC Length Rules
        if len(norm) > 254:
            raise EmailVerificationError(_msg("too_long", active_lang, field=field_name))
        if len(local_part) > 64:
            raise EmailVerificationError(_msg("local_too_long", active_lang))
        if not EMAIL_REGEX.match(norm):
            raise EmailVerificationError(_msg("invalid_rfc", active_lang, field=field_name))

        # Check for obvious random garbage patterns
        if re.search(r"^(?:asdf|qwerty|123456|testtest)", local_part.lower()):
            raise EmailVerificationError(_msg("garbage_pattern", active_lang, field=field_name, local=local_part))

        # 2. Disposable / Temp Mail Check
        if cls.is_disposable_domain(domain):
            raise EmailVerificationError(_msg("disposable_domain", active_lang, domain=domain))

        provider_type = "corporate"
        canonical = norm

        # 3. Google Personal Email Validation
        if domain in GOOGLE_DOMAINS:
            provider_type = "google_personal"
            canonical = cls.canonicalize_email(norm)
            clean_local = local_part.split("+")[0].replace(".", "").lower()

            if len(clean_local) < 6:
                raise EmailVerificationError(_msg("gmail_too_short", active_lang, local=clean_local))
            if len(clean_local) > 30:
                raise EmailVerificationError(_msg("gmail_too_long", active_lang, local=clean_local))

        # 4. Microsoft Personal Email Validation
        elif domain in MICROSOFT_DOMAINS:
            provider_type = "microsoft_personal"
            if len(local_part) < 2:
                raise EmailVerificationError(_msg("microsoft_too_short", active_lang, email=norm))

        # 5. MX Records & Mail Server Verification
        mx_servers: list[str] = []
        if check_mx:
            mx_servers = cls.query_mx_records(domain)
            if not mx_servers:
                raise EmailVerificationError(_msg("no_mx_server", active_lang, domain=domain))

            if provider_type == "google_personal":
                has_google_mx = any("google" in mx for mx in mx_servers)
                if not has_google_mx:
                    raise EmailVerificationError(_msg("google_mx_mismatch", active_lang, domain=domain))
            elif provider_type == "microsoft_personal":
                has_ms_mx = any("outlook.com" in mx or "protection.outlook" in mx for mx in mx_servers)
                if not has_ms_mx:
                    raise EmailVerificationError(_msg("ms_mx_mismatch", active_lang, domain=domain))
            else:
                if any("google" in mx for mx in mx_servers):
                    provider_type = "google_workspace"
                elif any("outlook" in mx for mx in mx_servers):
                    provider_type = "microsoft_365_enterprise"

        # 6. Optional SMTP Mailbox Probe
        probe_result: dict[str, Any] = {"probed": False, "status": "SKIPPED"}
        if check_mx and probe_smtp and mx_servers:
            probe_result = cls.probe_mailbox_smtp(canonical or norm, mx_servers[0])
            if probe_result.get("status") == "MAILBOX_NOT_FOUND":
                raise EmailVerificationError(_msg("mailbox_not_found", active_lang, domain=domain, email=norm))

        return {
            "valid": True,
            "email": norm,
            "canonicalEmail": canonical,
            "domain": domain,
            "providerType": provider_type,
            "mxServers": mx_servers,
            "smtpProbe": probe_result,
            "language": active_lang,
        }

    # -----------------------------------------------------------------------
    # Step 5: Active SMTP Mailbox Probe (Zero-Email Sent)
    # -----------------------------------------------------------------------
    @staticmethod
    def probe_mailbox_smtp(email: str, mx_host: str, timeout: float = 3.5) -> dict[str, Any]:
        try:
            server = smtplib.SMTP(mx_host, 25, timeout=timeout)
            server.helo("verify.forensics-suite.vn")
            server.mail("noreply-license@forensics-suite.vn")
            code, resp = server.rcpt(email)
            try:
                server.quit()
            except Exception:
                pass

            resp_str = resp.decode("utf-8", errors="replace") if isinstance(resp, bytes) else str(resp)

            if code == 250:
                return {"probed": True, "status": "VERIFIED_EXISTS", "code": code, "response": resp_str}
            elif code in (550, 551, 552, 553):
                return {"probed": True, "status": "MAILBOX_NOT_FOUND", "code": code, "response": resp_str}
            else:
                return {"probed": True, "status": "PROBE_INCONCLUSIVE", "code": code, "response": resp_str}
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, socket.timeout, Exception) as exc:
            return {"probed": True, "status": "PROBE_INCONCLUSIVE", "error": str(exc)}

    # -----------------------------------------------------------------------
    # Step 6: Challenge-Response OTP Verification (100% Ownership Proof)
    # -----------------------------------------------------------------------
    def generate_otp(self, email: str, expiry_minutes: int = 5) -> str:
        clean_email = self.normalize_email(email)
        otp = f"{random.SystemRandom().randint(100000, 999999)}"
        salt = os.urandom(8).hex()
        otp_hash = hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()
        expires_at = time.time() + (expiry_minutes * 60)

        cache = self._load_otp_cache()
        cache[clean_email] = {
            "hash": otp_hash,
            "salt": salt,
            "expiresAt": expires_at,
            "attempts": 0,
        }
        self._save_otp_cache(cache)
        return otp

    def verify_otp(self, email: str, candidate_otp: str) -> bool:
        clean_email = self.normalize_email(email)
        candidate = str(candidate_otp or "").strip()
        cache = self._load_otp_cache()

        record = cache.get(clean_email)
        if not record:
            return False

        if time.time() > record.get("expiresAt", 0):
            cache.pop(clean_email, None)
            self._save_otp_cache(cache)
            return False

        if record.get("attempts", 0) >= 3:
            cache.pop(clean_email, None)
            self._save_otp_cache(cache)
            return False

        record["attempts"] = record.get("attempts", 0) + 1
        expected_hash = hashlib.sha256(f"{record['salt']}:{candidate}".encode("utf-8")).hexdigest()

        if expected_hash == record["hash"]:
            cache.pop(clean_email, None)
            self._save_otp_cache(cache)
            return True

        self._save_otp_cache(cache)
        return False

    def send_otp_email(
        self,
        recipient_email: str,
        otp: str,
        *,
        client_name: str = "",
        smtp_config: dict[str, Any] | None = None,
        lang: str | None = None,
    ) -> tuple[bool, str]:
        active_lang = lang or self.language or _detect_system_language()
        clean_email = self.normalize_email(recipient_email)
        config = smtp_config or self._load_smtp_config()

        if not config or not config.get("host"):
            if active_lang == "en":
                msg = f"[SIMULATION MODE] Verification OTP generated: {otp} (Configure ~/.fdctl-secrets/smtp_config.json for live SMTP delivery)."
            else:
                msg = f"[SIMULATION MODE] Mã OTP đã được tạo: {otp} (Để gửi mail thật, hãy cấu hình ~/.fdctl-secrets/smtp_config.json)."
            return True, msg

        try:
            msg = EmailMessage()
            if active_lang == "en":
                msg["Subject"] = f"[Forensics Suite] License Verification Security Code: {otp}"
                body = f"""Dear {client_name or clean_email},

We received a request to issue or activate a software license for Forensics Suite for this email address.

YOUR 6-DIGIT VERIFICATION CODE (OTP):
========================================
           >>>  {otp}  <<<
========================================

* This code expires in 5 minutes.
* If you did not request a Forensics Suite license, please ignore this email.

Best regards,
Truong Trieu Vy (Azynora)
Lead Architect, Forensics Suite
Email: trieuvy9198@gmail.com
Repository: https://github.com/Azynora/Forensic-Tools
"""
            else:
                msg["Subject"] = f"[Forensics Suite] Mã xác nhận cấp bản quyền: {otp}"
                body = f"""Kính gửi {client_name or clean_email},

Chúng tôi đã nhận được yêu cầu cấp phát / xác thực bản quyền phần mềm Forensics Suite cho địa chỉ email này.

MÃ XÁC NHẬN (OTP) CỦA BẠN LÀ:
========================================
           >>>  {otp}  <<<
========================================

* Mã OTP có hiệu lực trong vòng 5 phút.
* Nếu bạn không yêu cầu cấp bản quyền Forensics Suite, vui lòng bỏ qua email này.

Trân trọng,
Trương Triệu Vỹ (Azynora)
Kỹ sư trưởng Kiến trúc Forensics Suite
Email: trieuvy9198@gmail.com
Website: https://github.com/Azynora/Forensic-Tools
"""
            msg["From"] = config.get("sender", config.get("user", "noreply@forensics-suite.vn"))
            msg["To"] = clean_email
            msg.set_content(body)

            host = config["host"]
            port = int(config.get("port", 587))
            use_ssl = config.get("use_ssl", False)
            user = config.get("user", "")
            password = config.get("password", "")

            if use_ssl or port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                server.starttls()

            if user and password:
                server.login(user, password)

            server.send_message(msg)
            server.quit()
            
            success_str = (
                f"OTP code has been successfully sent to {clean_email}."
                if active_lang == "en"
                else f"Mã OTP đã được gửi thành công tới {clean_email}."
            )
            return True, success_str
        except Exception as exc:
            err_str = (
                f"Failed to deliver email via SMTP: {exc}"
                if active_lang == "en"
                else f"Lỗi khi gửi email qua SMTP: {exc}"
            )
            return False, err_str

    def _load_smtp_config(self) -> dict[str, Any]:
        cfg_file = self.secrets_dir / "smtp_config.json"
        if cfg_file.exists() and cfg_file.is_file():
            try:
                return json.loads(cfg_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        env_host = os.environ.get("FDCTL_SMTP_HOST", "").strip()
        if env_host:
            return {
                "host": env_host,
                "port": int(os.environ.get("FDCTL_SMTP_PORT", 587)),
                "user": os.environ.get("FDCTL_SMTP_USER", "").strip(),
                "password": os.environ.get("FDCTL_SMTP_PASSWORD", "").strip(),
                "sender": os.environ.get("FDCTL_SMTP_SENDER", "").strip(),
                "use_ssl": os.environ.get("FDCTL_SMTP_SSL", "0") in ("1", "true", "True"),
            }
        return {}

    def _load_otp_cache(self) -> dict[str, Any]:
        if self.otp_cache_file.exists():
            try:
                return json.loads(self.otp_cache_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_otp_cache(self, cache: dict[str, Any]) -> None:
        try:
            self.secrets_dir.mkdir(parents=True, exist_ok=True)
            self.otp_cache_file.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        except Exception:
            pass
