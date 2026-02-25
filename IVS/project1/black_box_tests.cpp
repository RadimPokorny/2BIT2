//======= Copyright (c) 2025, FIT VUT Brno, All rights reserved. ============//
//
// Purpose:     Red-Black Tree - public interface tests
//
// $NoKeywords: $ivs_project_1 $black_box_tests.cpp
// $Author:     RADIM POKORNY <xpokorr00@stud.fit.vutbr.cz>
// $Date:       $2026-02-18
//============================================================================//
/**
 * @file black_box_tests.cpp
 * @author RADIM POKORNY
 * 
 * @brief Implementace testu binarniho stromu.
 */

#include <vector>

#include "gtest/gtest.h"

#include "red_black_tree.h"

//============================================================================//
// ** ZDE DOPLNTE TESTY **
//
// Zde doplnte testy Red-Black Tree, testujte nasledujici:
// 1. Verejne rozhrani stromu
//    - InsertNode/DeleteNode a FindNode
//    - Chovani techto metod testuje pro prazdny i neprazdny strom.
// 2. Axiomy (tedy vzdy platne vlastnosti) Red-Black Tree:
//    - Vsechny listove uzly stromu jsou *VZDY* cerne.
//    - Kazdy cerveny uzel muze mit *POUZE* cerne potomky.
//    - Vsechny cesty od kazdeho listoveho uzlu ke koreni stromu obsahuji
//      *STEJNY* pocet cernych uzlu.
//============================================================================//

TEST(EmptyTree, InsertNode) {
    BinaryTree tree;

    auto res = tree.InsertNode(10);

    EXPECT_TRUE(res.first); 
    
    ASSERT_NE(res.second, nullptr); 
    
    EXPECT_EQ(res.second->key, 10);
  
}

TEST(EmptyTree, DeleteNode) {
    BinaryTree tree;

    auto res = tree.DeleteNode(10);
    EXPECT_FALSE(res);
}

TEST(EmptyTree, FindNode) {
    BinaryTree tree;
    auto res = tree.FindNode(10);
    EXPECT_EQ(res, nullptr);
}

TEST(NonEmptyTree, InsertNode) {
    BinaryTree tree;
    tree.InsertNode(10); 
    auto res = tree.InsertNode(10);
    
    EXPECT_FALSE(res.first);     
    EXPECT_EQ(res.second->key, 10);

    auto res2 = tree.InsertNode(10);
    EXPECT_FALSE(res2.first);
    EXPECT_NE(res2.second, nullptr);
    if(res2.second != nullptr)
    EXPECT_EQ(res2.second->key, 10);  

    auto res3 = tree.InsertNode(20);
    EXPECT_TRUE(res3.first);      
}

TEST(NonEmptyTree, DeleteNode) {
    BinaryTree tree;
    tree.InsertNode(10);
    tree.InsertNode(20);
    EXPECT_TRUE(tree.DeleteNode(10));
    EXPECT_FALSE(tree.DeleteNode(10));

    EXPECT_NE(tree.FindNode(20), nullptr);
}

TEST(NonEmptyTree, FindNode) {
    BinaryTree tree;
    tree.InsertNode(30);
    tree.InsertNode(20);
    tree.InsertNode(60);
    tree.InsertNode(10);

    auto node = tree.FindNode(10);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->key,10);
    
    auto node2 = tree.FindNode(20);
    ASSERT_NE(node2, nullptr);
    EXPECT_EQ(node2->key,20);

    EXPECT_EQ(tree.FindNode(99), nullptr);
    
}

TEST(TreeAxioms, Axiom11) {
    BinaryTree tree;
    std::vector<std::pair<bool, BinaryTree::Node_t *>> out;
    tree.InsertNodes({10, 20, 30, 40, 50, 60, 70, 80, 90, 100}, out);
    std::vector<BinaryTree::Node_t *> leaves;
    tree.GetLeafNodes(leaves);

    ASSERT_FALSE(leaves.empty());

    for(auto node : leaves) {
        EXPECT_EQ(node->color, BinaryTree::BLACK);
    }
}

TEST(TreeAxioms, Axiom12) {
    BinaryTree tree;
    std::vector<BinaryTree::Node_t *> leaves;
    tree.GetLeafNodes(leaves);
    for(auto node : leaves) EXPECT_EQ(node->color, BinaryTree::BLACK);
    std::vector<std::pair<bool, BinaryTree::Node_t *>> out;
    tree.InsertNodes({50, 25, 75, 10, 35}, out);
    leaves.clear();
    tree.GetLeafNodes(leaves);
    
    ASSERT_FALSE(leaves.empty());
    for(auto node : leaves) {
        EXPECT_EQ(node->color, BinaryTree::BLACK);
    }
}

TEST(TreeAxioms, Axiom2) {
    BinaryTree tree;
    std::vector<std::pair<bool, BinaryTree::Node_t *>> out;
    tree.InsertNodes({10, 20, 30, 40, 50, 60, 70, 80, 90, 100}, out);
    std::vector<BinaryTree::Node_t *> nodes;
    tree.GetAllNodes(nodes);

    for (auto node : nodes) {
        if (node->color == BinaryTree::RED) {
            if (node->pLeft != nullptr) 
                EXPECT_EQ(node->pLeft->color, BinaryTree::BLACK);
            if (node->pRight != nullptr) 
                EXPECT_EQ(node->pRight->color, BinaryTree::BLACK);
        }
    }
}

TEST(TreeAxioms, Axiom3) {
    BinaryTree tree;
    std::vector<std::pair<bool, BinaryTree::Node_t *>> out;
    tree.InsertNodes({10, 20, 30, 40, 50, 60, 70, 80, 90, 100}, out);
    std::vector<BinaryTree::Node_t *> leaves;
    tree.GetLeafNodes(leaves);

    int black_count_reference = -1; 

    for (auto node : leaves) {
        int current_black_count = 0;
        BinaryTree::Node_t *current = node;

        while (current != nullptr) {
            if (current->color == BinaryTree::BLACK) {
                current_black_count++;
            }
            current = current->pParent;
        }

        if (black_count_reference == -1) {
            black_count_reference = current_black_count;
        } else {
            EXPECT_EQ(current_black_count, black_count_reference);
        }
    }
}

/*** Konec souboru black_box_tests.cpp ***/
