package dev.oxoo2a.sim4da.dsm;

import dev.oxoo2a.sim4da.Message;
import dev.oxoo2a.sim4da.Network;
import dev.oxoo2a.sim4da.Node;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * AP-Variante (Availability + Partition Tolerance).
 */
public class ApDsmNode extends Node implements Dsm {

    private final Map<String, String> local = new ConcurrentHashMap<>();

    public ApDsmNode(int myId, int totalNodes) {
        super(myId);
    }

    /* ====================== Thread-Loop ====================== */
    @Override
    public void main() {
        while (stillSimulating()) {

            Network.Message raw = receive();    // non-blocking
            if (raw == null) {
                Thread.yield();
                continue;
            }

            Message msg = Message.fromJson(raw.payload);
            String key   = msg.query("k");
            String value = msg.query("v");
            if (key != null && value != null)
                local.put(key, value);
        }
    }

    /* ====================== DSM-API ====================== */
    @Override
    public void write(String key, String value) {
        local.put(key, value);                  // lokal
        sendBroadcast(new Message().add("k", key).add("v", value));
    }

    @Override
    public String read(String key) {
        return local.get(key);
    }
}
