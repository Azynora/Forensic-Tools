# Version Changelog

## 1.2.0 - 2026-11-06

- added bilingual Tkinter app with Discord workflow, synthetic SAMPLE demo, case browser, license and workspace settings
- selecting Zalo now explains that support is under development and returns to Discord selection without closing the CLI/app
- enforced feature entitlements at collection and analysis service boundaries; trial licenses are limited to synthetic demo access
- added personal-project licensing with a local seven-day demo trial and owner-issued device-bound Ed25519 keys; no store account or payment backend required
- retained Ed25519 license verification for migration and added an Inno Setup per-user installer build target
- simplified bilingual GitHub README and quick installation/CLI guide

## 1.1.9 - 2026-11-06

- rút gọn README và hướng dẫn vận hành, bổ sung quick start tiếng Việt cùng giới hạn về chứng cứ và bảo vệ mã nguồn
- thêm README chọn tiếng Việt/Anh, requirements cho source/build và quy tắc loại trừ runtime, build, case data khỏi Git
- loại bỏ đường dẫn Python riêng của máy phát triển khỏi launcher và script build
- giới hạn case ID và xác nhận case path nằm trực tiếp trong workspace trước khi thao tác
- cập nhật package `fdctl` lên `0.2.9` và chuẩn bị repository source song ngữ
- xoay khóa ký cho bản phát hành mới, giữ public key cũ để xác thực các license đã cấp

## 1.1.8 - 2026-04-27

- stabilized public device binding by switching the primary machine fingerprint to a Windows-machine identity that no longer depends on the current username
- kept backward compatibility for previously activated keys by still accepting the legacy machine-hash path during verification
- canonicalized Gmail identities before trial and license matching so dotted and plus-tag Gmail variants resolve to the same licensed inbox identity
- rebuilt the bundle-only public release after the Gmail and device-binding fixes
- bumped Python package `fdctl` to `0.2.8`

## 1.1.7 - 2026-04-24

- added local `license_history.json` tracking for Gmail addresses, masked key previews, license labels, and recent activation/trial events
- improved the terminal activation flow so returning users can re-enter only their Gmail address when a valid local trial or activation already exists
- added legacy trial migration support so older `trial_3d_device` records can be adopted into the current Gmail-based trial model without silently losing the remaining trial period
- extended `license status` to include recent local license/email history for troubleshooting
- bumped Python package `fdctl` to `0.2.7`

## 1.1.6 - 2026-04-24

- removed the hard-coded owner master key from the public client path
- switched owner-only access to separately issued signed owner keys generated from the private source workspace
- removed `sourceCommit` from `BUILD_PROVENANCE.json` to reduce internal metadata exposure
- hardened bundle packaging so the build fails if any `.py`, `.ts`, `.tsx`, `.spec`, or `.toml` source files remain in the public runtime
- updated the portable public release workflow to target a source-free bundle layout
- bumped Python package `fdctl` to `0.2.6`

## 1.1.5 - 2026-04-24

- added `license machine` so end users can print their device name and machine fingerprint without extra guidance
- rebuilt the portable bundle after fixing runtime packaging so `fdctl_runtime.exe` and required Python DLL files are preserved in `dist`
- refreshed the public bundle snapshot and portable zip outputs
- bumped Python package `fdctl` to `0.2.5`

## 1.1.4 - 2026-04-24

- changed activation flow to Gmail-only addresses ending with `@gmail.com`
- replaced owner email bypass with a separate unlimited owner master key
- limited the free trial to the first Gmail address used on one device
- added device-bound customer licensing metadata for issued keys
- older customer keys should be re-issued because the compact license schema changed
- fixed the broken local `.venv` workflow by recreating it against a valid Python runtime
- default customer key output now uses `D:\ForensicWorkspace` when `--out` is omitted
- updated the terminal workspace info to show the device name and active email
- bumped Python package `fdctl` to `0.2.4`

## 1.1.3 - 2026-04-24

- added owner-email bypass so `trieuvy9198@gmail.com` can enter the registered email without a key
- a copied private source checkout on another device can now keep working after the owner email is entered once
- `license status` now accepts `--email` so the current email-specific access state can be checked directly
- bumped Python package `fdctl` to `0.2.3`

## 1.1.2 - 2026-04-24

- changed the free trial model from `3 days / 1 device` to `3 days / 1 email`
- the user must now enter an email address before the protected workflow can continue
- when the trial for that email expires, the terminal workflow asks for the issued key
- default issued key types are now `issued_7d`, `issued_30d`, and `issued_365d`

## 1.1.1 - 2026-04-24

- bumped the release metadata to `1.1.1`
- bumped Python package `fdctl` to `0.2.1`
- added visible version display to the terminal banner and workspace summary
- kept the terminal-only portable bundle model unchanged

## 1.1.0 - 2026-04-24

This release refactors `FORENSICS_DISCORD` back into a portable terminal-only DFIR toolkit for Windows 11.

### Highlights

- removed the GUI/app release path from the active product model
- retired the installer-based distribution path in favor of a portable CLI bundle
- removed the frontend web report dependency from the active workflow
- changed frozen/bundle workspace behavior to use `.\workspace` beside the portable bundle by default
- kept license and trial state under `%LOCALAPPDATA%\FORENSICS_DISCORD\license`
- changed `report open` into a terminal summary with canonical report paths
- updated bundle packaging to ship only `fdctl.cmd`, `fdctl.ps1`, `launch-analysis-terminal.cmd`, `activate-license.cmd`, the embedded runtime, and documentation
- prepared the public release model for bundle-only GitHub publication and GitHub Releases zip distribution

## 1.0.3 - 2026-04-21

This release focused on documentation cleanup, copyright marking, and preparing the repository for a cleaner private GitHub layout.

### Highlights

- added `COPYRIGHT_NOTICE.md` for ownership and contact details
- updated package metadata with the current author and contact information
- streamlined the GitHub-facing documentation layout
- added `USAGE_GUIDE.md` as the detailed English operating guide

## Current version snapshot

- operator release: `1.1.9`
- `fdctl`: `0.2.9`
- distribution: `portable-cli-bundle`
