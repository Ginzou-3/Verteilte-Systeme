package dev.oxoo2a.sim4da.dsm;

/** Consistency + Availability.  Keine Partitionstoleranz. */
public class CaDsm implements Dsm {

    private static final java.util.Map<String,String> master =
            new java.util.concurrent.ConcurrentHashMap<>();

    @Override public void write(String k, String v) { master.put(k, v); }
    @Override public String read(String k)           { return master.get(k); }
}
