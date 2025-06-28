package dev.oxoo2a.sim4da.dsm;

/** Gemeinsame API für alle DSM-Varianten. */
public interface Dsm {
    void write(String key, String value);
    String read(String key);
}