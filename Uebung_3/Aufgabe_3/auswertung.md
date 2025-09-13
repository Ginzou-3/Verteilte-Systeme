änder# Auswertung: Skalierbarkeit und Konsistenz bei MongoDB

## Messergebnisse (Beispiel)
Die Messreihe mit `measure_likes.py` zeigt, wie sich Durchsatz, Latenz und Konsistenzfehler bei steigender Worker-Zahl (Clustergröße) verändern. Typische Beobachtungen:
- **Durchsatz** steigt mit mehr Workern, bis die Datenbank oder das Netzwerk zum Flaschenhals wird.
- **Latenz** pro Operation bleibt anfangs niedrig, steigt aber bei sehr hoher Last.
- **Konsistenzfehler** (z.B. Like-Zahlen stimmen nicht sofort) treten bei schwacher Konsistenz häufiger auf, sind aber meist temporär.

## Wann lohnt sich horizontales Scaling?
- **Horizontale Skalierung** lohnt sich, wenn die Last (z.B. viele parallele Likes) die Kapazität eines einzelnen Servers übersteigt.
- Bei wenigen Workern ist der Overhead durch Verteilung höher als der Nutzen.
- Ab einer bestimmten Größe (z.B. >8 Worker) steigt der Gesamtdurchsatz deutlich, solange die Infrastruktur (Netzwerk, Sharding) mitwächst.

## Effekte reduzierter Konsistenz
- **Anwendungsebene:** Nutzer sehen evtl. nicht sofort alle Likes, da Reads von Secondaries verzögert sein können.
- **Benutzerebene:** Kurzfristige Inkonsistenzen (z.B. Like verschwindet kurzzeitig) sind möglich, aber für viele Social-Media-Anwendungen akzeptabel.
- **Fehlerhafte Reads** sind selten kritisch, solange die Datenbank eventual consistency garantiert.

## Best-Practice-Empfehlungen
1. **Shard-Key sorgfältig wählen:**
   - Wähle einen Shard-Key, der eine gleichmäßige Verteilung der Daten und Zugriffe ermöglicht, um Hotspots zu vermeiden.
2. **Konsistenzanforderungen anpassen:**
   - Setze Write-Concern und Read-Concern je nach Anwendungsfall. Für kritische Daten majority, für hohe Performance local/1.
3. **Monitoring und Fehlerbehandlung:**
   - Überwache das System auf Replikationsverzögerungen und Inkonsistenzen. Implementiere Mechanismen zur Fehlerkorrektur (z.B. Reconciliation-Jobs).

---

**Hinweis:** Die konkreten Zahlen und Effekte hängen von der Hardware, Netzwerktopologie und MongoDB-Konfiguration ab. Die bereitgestellten Skripte ermöglichen reproduzierbare Experimente und können für eigene Analysen angepasst werden.

