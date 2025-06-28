package dev.oxoo2a.sim4da;

import dev.oxoo2a.sim4da.dsm.*;
import org.apache.logging.log4j.LogManager;

import java.nio.file.*;

public class RunCounterApp {

    public static void main(String[] args) throws Exception {


        /* -------- Konfig per JVM-Properties -------- */
        int nNodes = Integer.parseInt(System.getProperty("nodes", "5"));
        int seconds = Integer.parseInt(System.getProperty("seconds", "20"));
        String variant = System.getProperty("variant", "AP").toUpperCase();

        System.out.println("VARIANT=" + System.getProperty("variant"));

        /* -------- Simulator anlegen (Original-API) -------- */
        Simulator sim = Simulator.createSimulator_Log4j2(nNodes);

        /* -------- Knoten erzeugen und anmelden -------- */
        for (int id = 0; id < nNodes; id++) {

            /* ----- 1) DSM-Instanz je nach Variante ----- */
            Dsm dsm;
            switch (variant) {
                case "AP" -> dsm = new ApDsmNode(id, nNodes);   // erbt von Node
                case "CP" -> dsm = new CpDsmNode(id, nNodes);   // erbt von Node
                case "CA" -> dsm = new CaDsm();                 // KEIN Node
                default    -> throw new IllegalArgumentException("variant = AP | CP | CA");
            }

            /* Simulator-Referenz setzen */
            if (dsm instanceof Node dsmNode) {
                dsmNode.setSimulator(sim);
                // >>> WICHTIG: DSM-Knoten als eigenen Thread beim Simulator anmelden
                sim.attachNode(id + nNodes, dsmNode);
            }

            /* ----- 2) Counter-App-Knoten ----- */
            CounterAppNode app = new CounterAppNode(id, nNodes, dsm);
            app.setSimulator(sim);

            /* App-Knoten läuft unter seiner "normalen" ID */
            sim.attachNode(id, app);
        }

        /* -------- Simulation ausführen -------- */
        sim.runSimulation(seconds);

        LogManager.shutdown();

        // 1) Parameter einlesen

        String latency = System.getProperty("s4da.latencyMs", "lat0");
        String partRaw = System.getProperty("s4da.partition", "nopart");

        // 2) Lesbare Tags bilden
        String partTag = partRaw.equals("nopart")
                ? "nopart"
                : "part" + Integer.toHexString(partRaw.hashCode());

        // 3) Dateinamen zusammensetzen
        String targetName = String.format("%s_%s_%s.log", variant, latency, partTag);

        Path src = Path.of("sim4da-app.log");
        Path dst = Path.of("logs", targetName);
        Files.createDirectories(dst.getParent());
        Files.move(src, dst, StandardCopyOption.REPLACE_EXISTING);

        System.out.println("Log gespeichert als " + dst);


    }
}
