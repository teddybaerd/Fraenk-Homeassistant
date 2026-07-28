# fraenk Mobile für Home Assistant

Inoffizielle Home-Assistant-Integration für den Mobilfunktarif von
[fraenk](https://fraenk.de/). Die Integration liest Datenvolumen, Verbrauch und
das Ende des aktuellen Abrechnungszeitraums aus der fraenk-App-API aus.

> [!IMPORTANT]
> Dies ist ein Community-Projekt und steht in keiner Verbindung zu fraenk,
> congstar oder der Deutschen Telekom. Die verwendete App-API ist nicht
> öffentlich dokumentiert und kann sich jederzeit ändern.

## Funktionen

- Einrichtung vollständig über die Home-Assistant-Oberfläche
- Unterstützung der SMS-mTAN bei der ersten Anmeldung
- Automatische Erneuerung der Anmeldung per Refresh-Token
- Automatische Reauthentifizierung über die Oberfläche, falls die Sitzung
  ungültig wird
- Aktualisierung im Abstand von 30 Minuten
- Unterstützung mehrerer Verträge und Datenpässe eines Kontos
- Diagnosedaten mit ausgeblendeten Konto-, Vertrags- und Tokenwerten

## Entitäten

Für jeden erkannten Vertrag bzw. Datenpass werden folgende Sensoren angelegt:

| Sensor | Beispiel |
| --- | ---: |
| Datenverbrauch | 10,44 GB |
| Verbleibendes Datenvolumen | 14,56 GB |
| Datenvolumen gesamt | 25 GB |
| Verbrauch | 42 % |
| Abrechnungszeitraum endet | 31.07.2026, 23:59:59 |
| Letzte Aktualisierung bei fraenk | standardmäßig deaktiviert |

## Installation über HACS

1. Öffne **HACS → Integrationen**.
2. Öffne das Menü oben rechts und wähle **Benutzerdefinierte Repositories**.
3. Trage die URL dieses GitHub-Repositorys ein.
4. Wähle als Kategorie **Integration**.
5. Installiere **fraenk Mobile** und starte Home Assistant neu.
6. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
7. Suche nach **fraenk Mobile** und melde dich an.
8. Gib die per SMS empfangene mTAN ein.

Alternativ kann der Ordner `custom_components/fraenk_mobile` manuell nach
`/config/custom_components/fraenk_mobile` kopiert werden.

## Datenschutz und Sicherheit

- Das fraenk-Passwort wird ausschließlich für Anmeldung oder
  Reauthentifizierung verwendet und nicht in Home Assistant gespeichert.
- Home Assistant speichert den Benutzernamen, die fraenk-Kunden-ID und den
  Refresh-Token im Config Entry.
- Access-Tokens werden nur im Arbeitsspeicher gehalten.
- Sämtliche API-Aufrufe erfolgen verschlüsselt direkt an `app.fraenk.de`.

Behandle ein Home-Assistant-Backup trotzdem vertraulich, da es den
Refresh-Token enthalten kann.

## Bekannte Einschränkungen

- Die Integration nutzt eine nicht öffentlich dokumentierte API.
- Änderungen an App oder Backend können ein Update der Integration erfordern.
- Eine neue SMS-mTAN kann erforderlich werden, wenn fraenk den Refresh-Token
  widerruft.
- Die in der App angezeigte Bezeichnung eines Datenpasses kann leer sein; dies
  beeinflusst die Sensorwerte nicht.

## Fehler melden

Erstelle ein GitHub-Issue und füge nach Möglichkeit die heruntergeladenen
Diagnosedaten der Integration bei. Entferne niemals manuell ausgegebene Tokens,
Passwörter oder vollständige API-Antworten aus privaten Debug-Werkzeugen.

## Lizenz

[MIT](LICENSE)

