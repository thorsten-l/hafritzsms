# AVM FRITZ!Box SMS für Home Assistant

[English version](README.md)

Die Integration **AVM FRITZ!Box SMS** verschickt SMS über eine AVM FRITZ!Box mit Mobilfunkmodem
(zum Beispiel FRITZ!Box 6850 5G, 6850 LTE, 6890 LTE). Sie spricht die Box lokal an. Die SMS geht
deshalb auch dann über das Mobilfunknetz raus, wenn die Internetverbindung ausgefallen ist. Damit
eignet sie sich gut als Rückfallkanal für wichtige Meldungen, etwa bei einem Stromausfall.

Dies ist ein Fork von [mback2k/hafritzsms](https://github.com/mback2k/hafritzsms).
Alle Änderungen stehen im [CHANGELOG](CHANGELOG.md).

## Funktionen

- Eine Benachrichtigungs-Entität pro Empfänger, nutzbar mit der Aktion `notify.send_message`.
- Anmeldung per PBKDF2 (FRITZ!OS 7.24+), MD5 als Rückfall für ältere Boxen.
- Der zweite Faktor (TOTP) wird bei jedem Versand automatisch bestätigt.
- Gesendete SMS werden danach aus dem Postausgang der FRITZ!Box gelöscht.
- Verständliche Fehlermeldungen in Home Assistant. Die Sitzung wird immer abgemeldet.
- Oberfläche auf Deutsch und Englisch.

## Voraussetzungen

- AVM FRITZ!Box mit eingebautem oder USB-Mobilfunkmodem und einer SIM-Karte, die SMS senden kann.
- Home Assistant 2026.8 oder neuer. Version 0.3.2 nutzt `via_device_id`, das erst seit 2026.8 existiert.
- Ein eigener FRITZ!Box-Benutzer mit App-basierter Zwei-Faktor-Anmeldung (TOTP).
  Jeder FRITZ!Box-Benutzer kann nur eine Authenticator-App haben, nimm also nicht dein persönliches Konto.

## Installation

### Schritt 1: Integration installieren

**Home Assistant 2026.11 und neuer (Marketplace)**

Seit 2026.11 hat der eingebaute Marketplace HACS abgelöst.

1. Den **Marketplace** öffnen und ein **benutzerdefiniertes Repository** hinzufügen (Menü mit den
   drei Punkten): `https://github.com/thorsten-l/hafritzsms`, Kategorie **Integration**.
2. Nach **AVM FRITZ!Box SMS** suchen und installieren.
3. Home Assistant neu starten.

**Home Assistant 2026.8 bis 2026.10 mit HACS**

1. **HACS** öffnen → Menü (drei Punkte) → **Benutzerdefinierte Repositories**.
2. Repository: `https://github.com/thorsten-l/hafritzsms`, Typ **Integration** → **Hinzufügen**.
3. Nach **AVM FRITZ!Box SMS** suchen, herunterladen und Home Assistant neu starten.

**Manuelle Installation**

1. Im Konfigurationsverzeichnis von Home Assistant den Ordner `custom_components/fritzsms` anlegen.
2. Alle Dateien dieses Repositorys hineinkopieren, auch den Ordner `translations`.
3. Home Assistant neu starten.

### Schritt 2: FRITZ!Box-Benutzer mit Zwei-Faktor-Anmeldung anlegen

1. In der Weboberfläche der FRITZ!Box anmelden.
2. **System → FRITZ!Box-Benutzer** öffnen und **Benutzer hinzufügen** klicken.
3. Einen Benutzernamen (zum Beispiel `homeassistant`) und ein sicheres Passwort vergeben.
4. Nur die Berechtigung **FRITZ!Box Einstellungen** erteilen. Weitere Rechte sind nicht nötig.
5. Den Benutzer speichern und anschließend erneut bearbeiten.
6. Die **Zwei-Faktor-Authentifizierung mit einer Authenticator-App** einschalten und als App-Namen
   `Home Assistant` eintragen.
7. Unter dem QR-Code das **Geheimnis als Text** anzeigen lassen und kopieren. Es besteht aus den
   Buchstaben A–Z und den Ziffern 2–7, zum Beispiel `JBSW Y3DP EHPK 3PXP`.
   **Wichtig:** Gebraucht wird dieses Geheimnis, nicht ein 6-stelliger Code aus einer App.
8. Die FRITZ!Box-Seite geöffnet lassen. Zum Abschluss fragt die Box nach einem aktuellen 6-stelligen
   Code. Diesen Code erzeugt Home Assistant in Schritt 3.

### Schritt 3: Integration in Home Assistant einrichten

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen und **AVM FRITZ!Box SMS** wählen.
2. Eintragen:
   - **Host**: IP-Adresse oder Hostname der FRITZ!Box, zum Beispiel `192.168.178.1`
   - **Benutzername** und **Passwort** des Benutzers aus Schritt 2
   - **Authenticator-Geheimnis (TOTP Secret)**: das Geheimnis aus Schritt 2.7 (Leerzeichen sind egal)
3. **Absenden** klicken.
   - Ist der zweite Faktor in der FRITZ!Box noch nicht abgeschlossen, erscheint die Meldung
     *„Für diesen Benutzer ist die App-basierte Zwei-Faktor-Anmeldung (TOTP) noch nicht
     eingerichtet“*. Unter dem Geheimnis-Feld steht dann der **aktuelle TOTP-Code**.
   - Diesen Code auf der offenen FRITZ!Box-Seite (Schritt 2.8) eingeben und die
     Zwei-Faktor-Einrichtung abschließen.
   - In Home Assistant erneut **Absenden** klicken. Die Integration ist jetzt eingerichtet.

### Schritt 4: Empfänger anlegen

1. **Einstellungen → Geräte & Dienste → AVM FRITZ!Box SMS** öffnen.
2. Beim Eintrag der FRITZ!Box über die drei Punkte **SMS-Empfänger hinzufügen** wählen.
3. Einen Namen (zum Beispiel `Thorsten SMS`) und die Handynummer im internationalen Format
   eintragen (zum Beispiel `+4917012345678`).
4. Jeder Empfänger wird zu einer eigenen Benachrichtigungs-Entität, zum Beispiel
   `notify.thorsten_sms`. Name und Nummer lassen sich später über **SMS-Empfänger ändern** anpassen.

### Schritt 5: Test-SMS senden

**Entwicklerwerkzeuge → Aktionen** öffnen, in den YAML-Modus wechseln und ausführen:

```yaml
action: notify.send_message
target:
  entity_id: notify.thorsten_sms
data:
  title: Home Assistant
  message: Test-SMS ueber die FRITZ!Box
```

Die SMS kommt als `Home Assistant: Test-SMS ueber die FRITZ!Box` an.

## Einsatz in Automationen

```yaml
- alias: Stromausfall per SMS
  triggers:
    - trigger: state
      entity_id: sensor.ups_status
      to: "OB"
  actions:
    # Die SMS zuerst senden: Sie kommt auch ohne Internet an. Andere Kanäle können bei
    # einem Ausfall scheitern, deshalb laufen sie mit continue_on_error weiter.
    - action: notify.send_message
      target:
        entity_id: notify.thorsten_sms
      data:
        message: "Stromausfall, USV seit {{ now().strftime('%H:%M') }} Uhr auf Batterie"
      continue_on_error: true
```

Tipps:

- Eine SMS fasst 160 Zeichen. Schon ein einziges Emoji oder Sonderzeichen (ä, ö, ü, €, …) stellt
  die ganze Nachricht auf Unicode um und senkt die Grenze auf 70 Zeichen. Texte also kurz und ohne
  Sonderzeichen halten, etwa „ue“ statt „ü“.
- SMS nur für wichtige Meldungen nutzen. Je nach Tarif kostet jede SMS Geld.

## Fehlersuche

| Meldung | Ursache und Lösung |
|---|---|
| *Das ist kein gültiges TOTP-Geheimnis* | Statt des Geheimnisses wurde ein 6-stelliger Code eingegeben. Das Geheimnis aus Schritt 2.7 eintragen. |
| *Für diesen Benutzer ist die App-basierte Zwei-Faktor-Anmeldung (TOTP) noch nicht eingerichtet* | Die Zwei-Faktor-Einrichtung in der FRITZ!Box mit dem Code unter dem Feld abschließen (Schritt 3.3). |
| *Anmeldung fehlgeschlagen (Benutzername oder Passwort falsch)* | Benutzername oder Passwort falsch, oder die FRITZ!Box sperrt nach mehreren Fehlversuchen die Anmeldung für eine Weile. |
| *Verbindung zur FRITZ!Box fehlgeschlagen* | Falscher Host, oder Home Assistant erreicht die FRITZ!Box nicht. |
| *SMS to … could not be sent: TOTP code was not accepted* | Die Uhr von Home Assistant oder der FRITZ!Box geht falsch. Beide brauchen die richtige Zeit (NTP). |

Mehr Details zeigt das Debug-Log:

```yaml
logger:
  logs:
    custom_components.fritzsms: debug
```

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md) (auf Englisch).

## Danksagung und Lizenz

- Ursprüngliche Integration und der Client `pyfritzsms` von [Marc Hörsken (@mback2k)](https://github.com/mback2k).
- Fork gepflegt von [@thorsten-l](https://github.com/thorsten-l).
- Lizenz: [Apache License 2.0](LICENSE).
