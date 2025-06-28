package dev.oxoo2a.sim4da.dsm;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Geteilte Utilities (lokaler Store, Logger ...) */
public abstract class AbstractDsm implements Dsm {

    /** Lokale Kopie – pro Knoten. */
    protected final Map<String,String> local = new ConcurrentHashMap<>();

    protected void debug(String msg) {
        System.out.printf("[DSM] %s%n", msg);
    }
}