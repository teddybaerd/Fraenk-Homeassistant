# GitHub-Veröffentlichung

## 1. Repository anlegen

Lege auf GitHub ein **öffentliches** Repository an, beispielsweise:

```text
ha-fraenk-mobile
```

Empfohlene Beschreibung:

```text
Inoffizielle fraenk-Mobile-Integration für Home Assistant und HACS
```

Empfohlene Topics:

```text
home-assistant
hacs
fraenk
custom-component
mobile-data
```

GitHub soll beim Anlegen keine zusätzliche README, `.gitignore` oder Lizenz
erzeugen, weil diese Dateien bereits enthalten sind.

## 2. Platzhalter ersetzen

Ersetze in
`custom_components/fraenk_mobile/manifest.json` dreimal
`DEIN-BENUTZERNAME` durch deinen GitHub-Benutzernamen. Falls das Repository
anders heißt, passe dort auch `ha-fraenk-mobile` an.

## 3. Dateien hochladen

Lade **den Inhalt dieses Ordners** in die oberste Ebene des Repositorys. Danach
müssen unter anderem diese Pfade direkt sichtbar sein:

```text
.github/workflows/validate.yml
custom_components/fraenk_mobile/manifest.json
hacs.json
README.md
LICENSE
```

Nicht nur das fertige ZIP und nicht den äußeren Ordner `fraenk-mobile-ha`
hochladen.

## 4. GitHub Actions prüfen

Öffne im Repository **Actions**. Die Prüfungen **HACS**, **Hassfest** und
**Python tests** sollten erfolgreich durchlaufen.

## 5. Erste Release erstellen

1. Öffne **Releases → Draft a new release**.
2. Erzeuge den Tag `v0.1.0`.
3. Release-Titel: `v0.1.0`.
4. Beschreibung beispielsweise:

   ```text
   Erste Version der fraenk-Mobile-Integration:
   - Anmeldung mit SMS-mTAN
   - automatischer Token-Refresh
   - Sensoren für Datenverbrauch und Abrechnungszeitraum
   ```

5. Veröffentliche das Release.

Eine eigene Source-Code-ZIP muss nicht hochgeladen werden. GitHub erzeugt die
Archive automatisch. HACS kann die normale Repository-Struktur verwenden.

## 6. In HACS testen

Füge die URL des Repositorys in HACS als benutzerdefiniertes Repository vom Typ
**Integration** hinzu. Installiere es, starte Home Assistant neu und füge danach
unter **Einstellungen → Geräte & Dienste** die Integration **fraenk Mobile**
hinzu.
