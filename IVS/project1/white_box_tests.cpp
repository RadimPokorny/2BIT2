//======= Copyright (c) 2026, FIT VUT Brno, All rights reserved. ============//
//
// Purpose:     White Box - test suite
//
// $NoKeywords: $ivs_project_1 $white_box_tests.cpp
// $Author:     RADIM POKORNY <xpokorr00@stud.fit.vutbr.cz>
// $Date:       $2026-02-18
//============================================================================//
/**
 * @file white_box_tests.cpp
 * @author RADIM POKORNY
 * 
 * @brief Implementace testu hasovaci tabulky.
 */

#include <vector>

#include "gtest/gtest.h"

#include "white_box_code.h"

//============================================================================//
// ** ZDE DOPLNTE TESTY **
//
// Zde doplnte testy hasovaci tabulky, testujte nasledujici:
// 1. Verejne rozhrani hasovaci tabulky
//     - Vsechny funkce z white_box_code.h
//     - Chovani techto metod testuje pro prazdnou i neprazdnou tabulku.
// 2. Chovani tabulky v hranicnich pripadech
//     - Otestujte chovani pri kolizich ruznych klicu se stejnym hashem 
//     - Otestujte chovani pri kolizich hashu namapovane na stejne misto v 
//       indexu
//============================================================================//

TEST(EmptyAutomat, EmptySize) {
    SuffixAutomaton suffix("");

    EXPECT_EQ(suffix.size(), 1);
}

TEST(EmptyAutomat, EmptyContains) {
    SuffixAutomaton suffix("");

    EXPECT_TRUE(suffix.contains(""));
}

TEST(SuffixAutomat, SimpleConstruction) {
    SuffixAutomaton suffix("abc");
    EXPECT_GE(suffix.size(), 4);
    EXPECT_LE(suffix.size(), 5);
    
    EXPECT_TRUE(suffix.contains(""));
}

TEST(SuffixAutomat, SimpleSearch){
    SuffixAutomaton suffix("barbarosa");
    EXPECT_TRUE(suffix.contains("barbarosa"));
    EXPECT_TRUE(suffix.contains("bar"));
    EXPECT_TRUE(suffix.contains("b"));
    EXPECT_TRUE(suffix.contains("a"));
    EXPECT_FALSE(suffix.contains("bro"));
    EXPECT_FALSE(suffix.contains("barbarosab"));
}

TEST(SuffixAutomat, SimpleStep){
    SuffixAutomaton suffix("baba");

    size_t next;
    EXPECT_TRUE(suffix.step(0, 'b', next));
    EXPECT_NE(next, 0);
}

TEST(SuffixAutomat, MultipleSteps) {
    SuffixAutomaton suffix("abc");
    size_t step1, step2, step3;
    ASSERT_TRUE(suffix.step(0, 'a', step1));
    ASSERT_TRUE(suffix.step(step1, 'b', step2));
    ASSERT_TRUE(suffix.step(step2, 'c', step3));
    EXPECT_EQ(suffix.get_state(step3).len, 3);
}

TEST(SuffixAutomat, OutOfRangeSize){
    SuffixAutomaton suffix("abc");
    EXPECT_THROW(suffix.get_state(suffix.size() + 1), std::out_of_range);
}

TEST(SuffixAutomat, GetState){
    SuffixAutomaton suffix("a");
    EXPECT_EQ(suffix.get_state(0).len, 0);
}

TEST(SuffixAutomat, OutOfRangeNext){
    SuffixAutomaton suffix("abc");
    EXPECT_THROW(suffix.next(30), std::out_of_range);
}

TEST(SuffixAutomat, NextReturn) {
    SuffixAutomaton suffix("abc");
    auto& transitions = suffix.next(0);
    ASSERT_FALSE(transitions.empty()); 
    EXPECT_EQ(transitions.at('a'), 1); 
}

TEST(SuffixAutomat, OutOfRangeLongest){
    SuffixAutomaton suffix("abc");
    EXPECT_THROW(suffix.longest_direct_continuation(5), std::out_of_range);
}

TEST(SuffixAutomat, LongestLinear){
    SuffixAutomaton suffix("abcd");
    // Here it should return "abcd", but returns "d" which is mistake
    EXPECT_EQ(suffix.longest_direct_continuation(0), "abcd");
}

TEST(SuffixAutomat, SimpleClear){
    SuffixAutomaton suffix("aba");
    suffix.clear();
    EXPECT_EQ(suffix.size(), 1);
}

TEST(SuffixAutomat, Rebuild) {
    SuffixAutomaton suffix("abc");
    suffix.clear();
    EXPECT_EQ(suffix.size(), 1);
    suffix.add_sequence("abc");
    EXPECT_TRUE(suffix.contains("c"));
}

TEST(SuffixAutomat, Sort){
    SuffixAutomaton suffix("abahaba");
    auto s_size = suffix.size();
    auto new_suf = suffix.topological_sort();

    // Found the bug, the length should be 1 point shorter
    EXPECT_EQ(s_size, new_suf.size()); 
    
    ASSERT_GT(new_suf.size(), 0);
    EXPECT_EQ(new_suf[0], 0);
}

/*** Konec souboru white_box_tests.cpp ***/
