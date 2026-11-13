# AVM FRITZ!Box SMS for Home Assistant

[Deutsche Version](README_de.md)

The **AVM FRITZ!Box SMS** integration sends SMS through an AVM FRITZ!Box with a cellular modem
(for example FRITZ!Box 6850 5G, 6850 LTE, 6890 LTE). It talks to the box locally, so messages
still go out over the mobile network when your internet connection is down. That makes it a good
fallback channel for critical alerts such as power failures.

This is a fork of [mback2k/hafritzsms](https://github.com/mback2k/hafritzsms).
All changes are listed in the [CHANGELOG](CHANGELOG.md).

## Features

- One notify entity per recipient, used with the `notify.send_message` action.
- Login with PBKDF2 (FRITZ!OS 7.24+), MD5 fallback for older boxes.
- Second factor (TOTP) is confirmed automatically on every send.
- Sent messages are deleted from the FRITZ!Box outbox afterwards.
- Clear error messages in Home Assistant. The session is always logged out.
- English and German user interface.

## Requirements

- AVM FRITZ!Box with internal or USB cellular modem and a SIM card that can send SMS.
- Home Assistant 2026.8 or newer (version 0.3.2 uses `via_device_id`, which was introduced in 2026.8).
- A dedicated FRITZ!Box user with app-based two-factor authentication (TOTP).
  Each FRITZ!Box user can only have one authenticator app, so do not use your personal account.

## Installation

### Step 1: Install the integration

**Home Assistant 2026.11 and newer (Marketplace)**

Since 2026.11, the built-in Marketplace has replaced HACS.

1. Open the **Marketplace** and add a **custom repository** (menu with the three dots):
   `https://github.com/thorsten-l/hafritzsms`, category **Integration**.
2. Search for **AVM FRITZ!Box SMS** and install it.
3. Restart Home Assistant.

**Home Assistant 2026.8 to 2026.10 with HACS**

1. Open **HACS** → menu (three dots) → **Custom repositories**.
2. Repository: `https://github.com/thorsten-l/hafritzsms`, type **Integration** → **Add**.
3. Search for **AVM FRITZ!Box SMS**, download it and restart Home Assistant.

**Manual installation**

1. Create the folder `custom_components/fritzsms` in your Home Assistant configuration directory.
2. Copy all files of this repository (including the `translations` folder) into it.
3. Restart Home Assistant.

### Step 2: Create a FRITZ!Box user with two-factor authentication

1. Log in to the FRITZ!Box web interface.
2. Go to **System → FRITZ!Box Users** and click **Add User**.
3. Enter a user name (for example `homeassistant`) and a strong password.
4. Grant only the permission **FRITZ!Box Settings**. No other rights are needed.
5. Save the user, then edit it again.
6. Enable **two-factor authentication with an authenticator app**. Enter `Home Assistant` as app name.
7. Click to reveal the **secret as text** below the QR code. It is a string of the letters A–Z and
   the digits 2–7, for example `JBSW Y3DP EHPK 3PXP`. Copy it.
   **Important:** you need this secret, not a 6-digit code from an app.
8. Keep this FRITZ!Box page open. The box asks for a current 6-digit code to finish the setup.
   Home Assistant generates this code in step 3.

### Step 3: Set up the integration in Home Assistant

1. Go to **Settings → Devices & Services → Add Integration** and select **AVM FRITZ!Box SMS**.
2. Enter:
   - **Host**: IP address or host name of the FRITZ!Box, for example `192.168.178.1`
   - **Username** and **Password** of the user from step 2
   - **TOTP secret**: the secret from step 2.7 (spaces are ignored)
3. Click **Submit**.
   - If the second factor is not finished on the FRITZ!Box yet, the form shows the error
     *"App-based second factor (TOTP) is not configured for this user yet"*. Below the
     secret field it shows the **current TOTP code**.
   - Enter this code on the open FRITZ!Box page (step 2.8) to finish the two-factor setup.
   - Click **Submit** again in Home Assistant. The integration is now set up.

### Step 4: Add recipients

1. Open **Settings → Devices & Services → AVM FRITZ!Box SMS**.
2. Click the three dots next to the FRITZ!Box entry → **Add SMS target**.
3. Enter a name (for example `Thorsten SMS`) and the mobile number in international format
   (for example `+4917012345678`).
4. Each recipient becomes its own notify entity, for example `notify.thorsten_sms`.
   Names and numbers can be changed later with **Update SMS target**.

### Step 5: Send a test message

Open **Developer Tools → Actions**, switch to YAML mode and run:

```yaml
action: notify.send_message
target:
  entity_id: notify.thorsten_sms
data:
  title: Home Assistant
  message: Test SMS via FRITZ!Box
```

The SMS arrives as `Home Assistant: Test SMS via FRITZ!Box`.

## Usage in automations

```yaml
- alias: Power failure via SMS
  triggers:
    - trigger: state
      entity_id: sensor.ups_status
      to: "OB"
  actions:
    # Send the SMS first: it works without internet. Other channels may fail
    # during an outage, so let them continue on error.
    - action: notify.send_message
      target:
        entity_id: notify.thorsten_sms
      data:
        message: "Power failure, UPS on battery since {{ now().strftime('%H:%M') }}"
      continue_on_error: true
```

Tips:

- An SMS holds 160 characters. A single emoji or special character (ä, ö, ü, €, …) switches the
  whole message to Unicode and reduces the limit to 70 characters. Keep texts short and plain.
- Use SMS only for important alerts. Depending on your tariff, every SMS may cost money.

## Troubleshooting

| Message | Cause and solution |
|---|---|
| *This is not a valid TOTP secret* | A 6-digit code was entered instead of the secret. Enter the text secret from step 2.7. |
| *App-based second factor (TOTP) is not configured for this user yet* | Finish two-factor setup on the FRITZ!Box with the code shown below the field (step 3.3). |
| *Invalid authentication* | Wrong user name or password, or the FRITZ!Box blocks logins for a while after several failed attempts. |
| *Failed to connect* | Wrong host or the FRITZ!Box is not reachable from Home Assistant. |
| *SMS to … could not be sent: TOTP code was not accepted* | The clock of Home Assistant or the FRITZ!Box is off. Both need the correct time (NTP). |

For details, enable debug logging:

```yaml
logger:
  logs:
    custom_components.fritzsms: debug
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Credits and license

- Original integration and the `pyfritzsms` client by [Marc Hörsken (@mback2k)](https://github.com/mback2k).
- Fork maintained by [@thorsten-l](https://github.com/thorsten-l).
- Licensed under the [Apache License 2.0](LICENSE).
