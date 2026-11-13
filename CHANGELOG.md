# Changelog

This project follows [Semantic Versioning](https://semver.org/).
Versions up to 0.2.1 come from the original repository
[mback2k/hafritzsms](https://github.com/mback2k/hafritzsms). This fork starts at 0.3.0.

## [0.3.2] - 2026-11-13

### Fixed

- Device registration uses `via_device_id` instead of the deprecated
  `DeviceInfo(via_device=...)`, which stops working in Home Assistant 2027.8.

## [0.3.1] - 2026-11-13

### Fixed

- Setup no longer fails with "Unknown error occurred" when a 6-digit TOTP code is
  entered instead of the TOTP secret. The secret is validated as base32 and the field
  shows a clear error message (`invalid_secret`).

### Changed

- Login and TOTP checks during setup moved into a separate helper method.

## [0.3.0] - 2026-11-13

### Added

- German translation (`translations/de.json`).
- Error message `totp_not_configured` if the FRITZ!Box user has no app-based second
  factor yet.
- Duplicate setups of the same box/user combination are rejected (unique id).
- The `title` of `notify.send_message` is prepended to the SMS text (`Title: Message`).

### Changed

- The FRITZ!Box client (formerly the PyPI package `pyfritzsms` 0.1.4 by @mback2k,
  Apache-2.0) is vendored as `fritzbox.py`. Requirements are now `pyotp` and
  `phonenumberslite`.
- Login uses PBKDF2 (challenge version 2, FRITZ!OS 7.24+) and falls back to MD5 for
  older boxes. The PBKDF2 calculation runs in the executor.
- Dedicated exception classes (connection, authentication, second factor, SMS). Errors
  show up in Home Assistant as a `HomeAssistantError` with a readable message instead of
  `KeyError`/`RuntimeError`.
- The session is always logged out, even on errors. Parallel sends to several targets are
  serialised with a lock.
- Manifest: code owner, documentation and issue tracker point to this fork.

## [0.2.1] - 2025-05-10

### Fixed

- Updated `pyfritzsms` with a fix for `KeyError: 'delete'`.

## [0.2.0] - 2025-05-09

### Changed

- Fixed and improved the ConfigSubentryFlow for SMS recipients, target reconfiguration
  and device registration.
- Updated dependencies, code formatted with ruff, GitHub workflows for ruff and releases.

## [0.1.2] - 2025-03-31

### Added

- TOTP generation during integration setup.

## [0.1.1] - 2025-03-28

- Initial version.

[0.3.2]: https://github.com/thorsten-l/hafritzsms/compare/e49ff0b...24b58cb
[0.3.1]: https://github.com/thorsten-l/hafritzsms/compare/0081661...e49ff0b
[0.3.0]: https://github.com/thorsten-l/hafritzsms/compare/b8a2eb5...0081661
[0.2.1]: https://github.com/mback2k/hafritzsms/commit/b8a2eb5
[0.2.0]: https://github.com/mback2k/hafritzsms/commit/6061253
[0.1.2]: https://github.com/mback2k/hafritzsms/commit/91f9197
[0.1.1]: https://github.com/mback2k/hafritzsms/commit/e9c958f
