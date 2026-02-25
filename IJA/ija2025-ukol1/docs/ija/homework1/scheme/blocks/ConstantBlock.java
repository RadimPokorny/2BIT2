/*
 * IJA (Seminář Java): 2025/26 Ukol 1
 * Author:  Radek Kočí, VUT FIT
 * Created: 02/2026
 */
package ija.homework1.scheme.blocks;

import java.util.Map;

/**
 * Blok reprezentující konstantní hodnotu. Hodnota je předána konstruktorem, lze ji změnit metodou.
 * Po vynucení výpočtu nebo nastavení nové hodnoty ukládá tuto hodnotu do výstupního portu.
 */
public class ConstantBlock extends Block {

    private double value;

    /**
     * Vytvoří instanci bloku pro konstantu.
     * @param name Název blok
     * @param value Nastavovaná hodnota.
     * @throws IllegalArgumentException pokud není zadán název bloku
     */
    public ConstantBlock(String name, double value) {
        super(name);
        this.value = value;
        getOutputPort().setValue(value); // okamžitá propagace
    }

    /**
     * Umožní nastavit interní hodnotu bloku, která se následně propaguje přes výstupní port.
     * @param value Nastavovaná hodnota.
     */
    @Override
    public void setValue(double value) {
        this.value = value;
        getOutputPort().setValue(value);
    }

}