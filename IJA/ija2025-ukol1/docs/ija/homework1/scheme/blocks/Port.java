/*
 * IJA (Seminář Java): 2025/26 Ukol 1
 * Author:  Radek Kočí, VUT FIT
 * Created: 02/2026
 */
package ija.homework1.scheme.blocks;

import java.util.ArrayList;
import java.util.List;

/**
 * Abstraktní třída reprezentující port bloku.
 * Každý port má název a vlastníka (blok) a uchovává informaci o poslední hodnotě.
 * Implicitní hodnota (pokud ještě nebyla žádná nastavena) je 0.
 * Vstupní port bloku je možné napojit na výstupní port jiného bloku, příp. jiných bloků.
 * Port pracuje s jedinou hodnotou typu double.
 */
public abstract class Port {

    /** Název portu (např. "a", "b", "out") */
    private String name;

    /** Blok, kterému port patří */
    private Block owner;

    /**
     * Vstupní port bloku.
     * Přijímá hodnotu z výstupního portu jiného bloku, po každém přijetí vyvolá přepočet svého bloku ({@link Block#calculate()}).
     */
    public static class InputPort extends Port {

        private Double value = 0.0; // poslední přijatá hodnota
        private OutputPort source;

        /**
         * Připojí vstupní port na výstupní blok zadaného bloku.
         * @param block Blok, na jehož výstupní port se připojí tento vstupní port.
         * @throws IllegalArgumentException pokud je block == null.
         */
        public void connect(Block block) {
            if (block == null) throw new IllegalArgumentException("Block cannot be null.");
            this.source = block.getOutputPort();
            source.addConnection(this);
        }

    }

    /**
     * Výstupní port bloku.
     * Při každém přepočtu (změně výsledku) bloku se nová hodnota uchová ve výstupním portu a propaguje se do připojených 
     * vstupních portů jiných bloků.
     */
    public static class OutputPort extends Port {

        private double value;
        private List<InputPort> connections = new ArrayList<>();

        /**
         * Vrátí aktuální hodnotu výstupního portu. 
         * @return Hodnota portu.
         */
        public double getValue() {
            return value;
        }
    }
}
