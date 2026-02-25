/*
 * IJA (Seminář Java): 2025/26 Ukol 1
 * Author:  Radek Kočí, VUT FIT
 * Created: 02/2026
 */
package ija.homework1.scheme.blocks;

import java.util.Map;

/** 
 * Blok provádějící násobení dvou vstupů. Vstupní porty jsou pojmenované "a" a "b".
 * Po provedení výpočtu ukládá do výstupního portu výsledek a * b.
 */
public class MultiplyBlock extends Block {
    /**
     * Vytvoří instanci bloku pro násobení.
     * @param name Název blok
     * @throws IllegalArgumentException pokud není zadán název bloku
     */
    public MultiplyBlock(String name) { super(name, "a", "b"); }

}
