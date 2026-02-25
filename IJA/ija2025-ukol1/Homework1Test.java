/*
 * IJA (Seminář Java): 2025/26 Ukol 1
 * Author:  Radek Kočí, VUT FIT
 * Created: 02/2026
 */
package ija.homework1.scheme;

import ija.homework1.scheme.blocks.AddBlock;
import ija.homework1.scheme.blocks.Block;
import ija.homework1.scheme.blocks.ConstantBlock;
import ija.homework1.scheme.blocks.MultiplyBlock;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Testovaci trida pro Ukol1.
 * @author koci
 */
public class Homework1Test {
    
    private Block c1;
    private Block c2;
    private Block c3;
    private Block add;
    private Block multiply;

    /**
     * Test vytvoreni a spravne funkce bloku pro scitani. 
     * 1 b.
     */
    @Test
    public void testAddBlockCalculation() {
        c1 = new ConstantBlock("c1", 5);
        c2 = new ConstantBlock("c2", 3);

        add = new AddBlock("add");
        assertEquals("add", add.getName(), "Block name is add.");

        // Zadny prepocet, vystup = 0
        assertEquals(0.0, add.getOutputPort().getValue());
        
        // Pripojeni vstupu, bez propagace hodnot
        // Zadny prepocet, vystup = 0
        add.getInputPort("a").connect(c1);
        assertEquals(0.0, add.getOutputPort().getValue());

        // Vyvolani prepoctu bloku: calculate()
        // Zadny prepocet, nejsou zapojeny vsechny vstupy, vystup = 0
        add.calculate();
        assertEquals(0.0, add.getOutputPort().getValue());
        
        // Pripojeni vstupu, bez propagace hodnot
        // Zadny prepocet, vystup = 0
        add.getInputPort("b").connect(c2);
        assertEquals(0.0, add.getOutputPort().getValue());
        
        // Prepocet nad c1 vynuti propagaci vystupniho portu na vsechny pripojene
        // Zmena na vstupu add.a=5, 5+0=5;
        c1.calculate();
        assertEquals(5, add.getOutputPort().getValue());

        // Zmena na vstupu b = 3, 5+3=8
        c2.calculate();        
        assertEquals(8, add.getOutputPort().getValue());
    }   
    
    /**
     * Test vytvoreni a spravne funkce schematu.
     * Bloky add = c1 + c2; multiply = add * c3. 
     * 1 b.
     */
    @Test
    public void testSchemeCalculation() {
        c1 = new ConstantBlock("c1", 5);
        c2 = new ConstantBlock("c2", 3);
        c3 = new ConstantBlock("c3", 2);

        add = new AddBlock("add");
        add.getInputPort("a").connect(c1);
        add.getInputPort("b").connect(c2);
        
        multiply = new MultiplyBlock("multiply");
        multiply.getInputPort("a").connect(add);
        multiply.getInputPort("b").connect(c3);
        
        // Zmena na vstupech: (5+3)=8; (8*3)=16
        c1.calculate();
        c2.calculate();
        c3.calculate();
        assertEquals(8, add.getOutputPort().getValue());     
        assertEquals(16, multiply.getOutputPort().getValue());
    }    

    /**
     * Test vytvoreni a spravne funkce schematu - prepocet po vynucene zmene hodnoty.
     * Bloky add = c1 + c2; multiply = add * c3. 
     * 1 b.
     */
    @Test
    public void testSchemeCalculation2() {
        c1 = new ConstantBlock("c1", 5);
        c2 = new ConstantBlock("c2", 3);
        c3 = new ConstantBlock("c3", 2);

        add = new AddBlock("add");
        add.getInputPort("a").connect(c1);
        add.getInputPort("b").connect(c2);
        
        multiply = new MultiplyBlock("multiply");
        multiply.getInputPort("a").connect(add);
        multiply.getInputPort("b").connect(c3);
        
        // Zmena na vstupech: (5+3)=8; (8*3)=16
        c1.calculate();
        c2.calculate();
        c3.calculate();
        assertEquals(8, add.getOutputPort().getValue());     
        assertEquals(16, multiply.getOutputPort().getValue());
        
        // zmena hodnoty c1=10, vysledek add: 10+3=13; multiply 13*2=26
        c1.setValue(10);
        assertEquals(13, add.getOutputPort().getValue());     
        assertEquals(26, multiply.getOutputPort().getValue());
    } 
    
    /**
     * Test vytvoreni a spravne funkce schematu - napojeni vystupniho portu na vice vstupnich portu. 
     * Bloky add = c1 + c2; multuply = c1 * c2.
     * 1 b.
     */
    @Test
    public void testSchemeCalculation3() {
        c1 = new ConstantBlock("c1", 5);
        c2 = new ConstantBlock("c2", 3);

        add = new AddBlock("add");
        add.getInputPort("a").connect(c1);
        add.getInputPort("b").connect(c2);
        
        multiply = new MultiplyBlock("multiply");
        multiply.getInputPort("a").connect(c1);
        multiply.getInputPort("b").connect(c2);
        
        // Zmena na vstupech: (5+3)=8; (5*3)=15
        c1.calculate();
        c2.calculate();
        assertEquals(8, add.getOutputPort().getValue());     
        assertEquals(15, multiply.getOutputPort().getValue());
    }       
    
    
    /**
     * Test generovani vyjimek pri chybnych argumentech.
     * 1 b.
     */
    @Test
    public void testBlockConstructorThrowsIfNoName() {
        // Blok bez jména by měl vyhodit IllegalArgumentException
        assertThrows(
            IllegalArgumentException.class,
            () -> new Block(null, "a", "b") {
                @Override
                protected double compute(Map<String, Double> inputs) {
                    return 0;
                }
            }, 
            "Block name cannot be null."
        );

        add = new AddBlock("add");
        assertThrows(
            IllegalArgumentException.class,
            () -> add.getInputPort("wrong name"),
            "Port name does not exist."
        );

        assertThrows(
            UnsupportedOperationException.class,
            () -> add.setValue(0),
            "AddBlock does not support the operation setValue."
        );

    }
}
