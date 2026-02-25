/*
 * IJA (Seminář Java): 2025/26 Ukol 1
 * Author:  Radek Kočí, VUT FIT
 * Created: 02/2026
 */
package ija.homework1.scheme.blocks;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Abstraktní třída reprezentující blok ve schématu.
 * Blok obsahuje vstupní porty a jeden výstupní port. Vstupních portů může být víc, nemusí být žádný (pro konstantu).
 * Bloky se propojují do schématu prostřednictvím portů, vizte {@link Port}.
 * Po každé změně vstupu dojde k automatickému přepočtu bloku a generování výstupu.
 * Přepočet je možné také vynutit voláním metody {@link #calculate()}.
 * Výpočty pracují s hodnotami typu double.
 */
public abstract class Block {

    private String name;
    private Map<String, Port.InputPort> inputPorts;
    private Port.OutputPort outputPort;

    /**
     * Konstruktor pro inicializaci bloku. Vytvoří odpovídající vstupní porty a výstupní port.
     * @param name Název blok
     * @param inputNames Seznam názvů vstupních portů
     * @throws IllegalArgumentException pokud není zadán název bloku
     */
    public Block(String name, String... inputNames) {
        if (name == null) throw new IllegalArgumentException("Block name cannot be null.");
        this.name = name;
        this.inputPorts = new LinkedHashMap<>();

        for (String inputName : inputNames) {
            inputPorts.put(inputName, new Port.InputPort(inputName, this));
        }

        this.outputPort = new Port.OutputPort("out", this);
    }

    /**
     * Vrací název bloku.
     * @return Název bloku.
     */
    public String getName() { return name; }

    //public Map<String, Port.InputPort> getInputPorts() { return inputPorts; }
    
    /**
     * Vrací vstupní port odpovídající názvu. Pokud v bloku není port daného jména, generuje výjimku.
     * @param name Název vstupního portu.
     * @return Vstupní port.
     * @throws IllegalArgumentException pokud port neexistuje.
     */
    public Port.InputPort getInputPort(String name) {
        if (!inputPorts.containsKey(name)) throw new IllegalArgumentException("Port name does not exist.");
        return inputPorts.get(name);
    }

    /**
     * Vrací výstupní port bloku.
     * @return Výstupní port.
     */
    public Port.OutputPort getOutputPort() { return outputPort; }

    /**
     * Provede výpočet bloku.
     * Pokud nejsou všechny vstupy připojeny, výpočet se neprovede.
     * Načte hodnoty ze vstupních portů, provede výpočet a výsledek vloží do výstupního portu.
     */
    public void calculate() {
        for (Port.InputPort port : inputPorts.values()) {
            if (!port.isConnected()) return;
        }

        Map<String, Double> inputValues = new LinkedHashMap<>();
        for (Map.Entry<String, Port.InputPort> entry : inputPorts.entrySet()) {
            inputValues.put(entry.getKey(), entry.getValue().getValue());
        }

        double result = compute(inputValues);
        outputPort.setValue(result);
    }

    /**
     * Umožní nastavit interní hodnotu bloku, která se následně propaguje přes výstupní port.
     * Má význam pouze pro některé bloky, implicitní implementace generuje výjimku. Odvozené třídy musí přepsat, pokud metodu potřebují.
     * @param value Nastavovaná hodnota.
     * @throws UnsupportedOperationException pro implicitní implementaci.
     */
    public void setValue(double value) {
        throw new UnsupportedOperationException("setValue()");
    }

    /**
     * Abstraktní metoda provádějící vlastní výpočet.
     *
     * @param inputs mapa (název vstupu -> hodnota)
     * @return vypočtená hodnota
     */
}
