package dev.oxoo2a.sim4da;

import dev.oxoo2a.sim4da.dsm.Dsm;
import dev.oxoo2a.sim4da.Tracer;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Counter-App: Jeder Knoten inkrementiert einen eigenen Zähler im DSM
 * und prüft auf Divergenzen zwischen allen Knoten.
 *
 * Inkonsistenzen werden per emit(...) im Simulator-Log mit dem Präfix
 * "ANOMALY@" ausgegeben, so dass sie leicht gefiltert werden können.
 */
public class CounterAppNode extends Node {

    /* ----------------------------------------------------
       Konfiguration & Zustand
       ---------------------------------------------------- */
    private final int                totalNodes;
    private final Dsm                dsm;
    private final String             myKey;
    private       int                localCounter = 0;
    private final Map<String,Integer> lastSeen    = new ConcurrentHashMap<>();

    public CounterAppNode(int myId, int totalNodes, Dsm dsm) {
        super(myId);
        this.totalNodes = totalNodes;
        this.dsm        = dsm;
        this.myKey      = "counter_" + myId;
        this.dsm.write(myKey, "0");           // Initialwert für alle sichtbar
    }

    /* ----------------------------------------------------
       Pflichtmethode aus Node  – Haupt-Thread
       ---------------------------------------------------- */
    @Override
    public void main() {

        while (stillSimulating()) {

            /* 1) eigenen Zähler erhöhen und schreiben */
            localCounter++;
            dsm.write(myKey, Integer.toString(localCounter));

            /* 2) alle Zähler lesen und auf Anomalien prüfen */
            for (int id = 0; id < totalNodes; id++) {
                String key = "counter_" + id;
                String valStr = dsm.read(key);

                if (valStr == null) {
                    logAnomaly("Missing value for " + key);
                    continue;
                }

                int valInt;
                try {
                    valInt = Integer.parseInt(valStr);
                } catch (NumberFormatException nfe) {
                    logAnomaly("Non-integer value for " + key + ": " + valStr);
                    continue;
                }

                Integer prev = lastSeen.get(key);
                if (prev != null && valInt < prev) {
                    logAnomaly(String.format(
                            "Non-monotonic value for %s: %d → %d", key, prev, valInt));
                }
                lastSeen.put(key, valInt);
            }

            /* 3) eine ganz kurze Pause, um CPU zu schonen */
            try { Thread.sleep(10); } catch (InterruptedException ignored) {}
        }
    }

    /* ----------------------------------------------------
       Logging mit log4j2
       ---------------------------------------------------- */
    private void logAnomaly(String msg) {
        emit("ANOMALY@Node-%d: %s", myId, msg);
    }
}
