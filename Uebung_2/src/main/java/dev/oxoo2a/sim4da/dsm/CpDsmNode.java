package dev.oxoo2a.sim4da.dsm;

import dev.oxoo2a.sim4da.Message;
import dev.oxoo2a.sim4da.Network;
import dev.oxoo2a.sim4da.Node;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * CP-Variante (Consistency + Partition Tolerance) mit einfachem Quorum-Commit.
 */
public class CpDsmNode extends Node implements Dsm {

    /* ---------- State ---------- */
    private final int totalNodes;
    private final int quorum;
    private final Map<String, String>             local  = new ConcurrentHashMap<>();
    private final Map<String, Set<Integer>> ackMap = new ConcurrentHashMap<>();

    public CpDsmNode(int myId, int totalNodes) {
        super(myId);
        this.totalNodes = totalNodes;
        this.quorum     = totalNodes / 2 + 1;
    }

    /* ====================== Thread-Loop ====================== */
    @Override
    public void main() {
        while (stillSimulating()) {

            Network.Message raw = receive();          // non-blocking
            if (raw == null) {
                Thread.yield();
                continue;
            }

            Message msg = Message.fromJson(raw.payload);
            handleIncoming(raw.sender_id, msg);
        }
    }

    /* ====================== DSM-API ====================== */
    @Override
    public synchronized void write(String key, String value) {
        String tx = UUID.randomUUID().toString();
        ackMap.put(tx, new HashSet<>(List.of(myId)));        // eigenes ACK

        sendBroadcast(new Message()
                .add("type", "W")
                .add("tx",   tx)
                .add("key",  key)
                .add("val",  value));                        // Write-Req

        awaitQuorum(tx);                                     // blockiert
        local.put(key, value);                               // Commit
    }

    @Override
    public synchronized String read(String key) {
        return local.get(key);
    }

    /* ====================== Message-Handling ====================== */
    private synchronized void handleIncoming(int from, Message msg) {

        switch (msg.query("type")) {

            case "W" -> {                         // Fremd-Write
                String tx  = msg.query("tx");
                String key = msg.query("key");
                String val = msg.query("val");
                local.put(key, val);

                sendUnicast(from, new Message()
                        .add("type", "ACK")
                        .add("tx",   tx));
            }

            case "ACK" -> {                       // Quorum-ACK
                String tx = msg.query("tx");
                ackMap.computeIfAbsent(tx, t -> new HashSet<>()).add(from);
                notifyAll();
            }
        }
    }

    /* ====================== Hilfs-Routine ====================== */
    private void awaitQuorum(String tx) {
        try {
            while (ackMap.get(tx).size() < quorum)
                wait(20);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            ackMap.remove(tx);
        }
    }
}
