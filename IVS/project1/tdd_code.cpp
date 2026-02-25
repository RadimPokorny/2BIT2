//======= Copyright (c) 2025, FIT VUT Brno, All rights reserved. ============//
//
// Purpose:     Test Driven Development - graph
//
// $NoKeywords: $ivs_project_1 $tdd_code.cpp
// $Author:     RADIM POKORNY <xpokorr00@stud.fit.vutbr.cz>
// $Date:       $2025-02-19
//============================================================================//
/**
 * @file tdd_code.cpp
 * @author Martin Dočekal
 * @author Karel Ondřej
 *
 * @brief Implementace metod tridy reprezentujici graf.
 */

#include "tdd_code.h"


Graph::Graph(){}

Graph::~Graph() {
    clear();
}

std::vector<Node*> Graph::nodes() {
    return m_nodes;
}

std::vector<Edge> Graph::edges() const{
    return m_edges;
}

Node* Graph::addNode(size_t node_id) {
    if (getNode(node_id) != nullptr) return nullptr;

    Node* new_node = new Node;
    new_node->color = 0;
    new_node->id = node_id;

    m_nodes.push_back(new_node);
    return new_node;
}

bool Graph::addEdge(const Edge& edge) {
    if (edge.a == edge.b) return false;
    if (containsEdge(edge)) return false;

    if (getNode(edge.a) == nullptr) addNode(edge.a);
    if (getNode(edge.b) == nullptr) addNode(edge.b);

    m_edges.push_back(edge);
    return true;
}

void Graph::addMultipleEdges(const std::vector<Edge>& edges) {
    for (const auto& e : edges) {
        addEdge(e);
    }
}

Node* Graph::getNode(size_t node_id){
    for (auto node : m_nodes) {
        if (node->id == node_id) return node;
    }
    return nullptr;
}

bool Graph::containsEdge(const Edge& edge) const{
    for (const auto& se : m_edges) {
        if (se == edge) return true;
    }
    return false;
}

void Graph::removeNode(size_t node_id){
    for (auto x = m_edges.begin(); x != m_edges.end(); ) {
        if (x->a == node_id || x->b == node_id) {
            x = m_edges.erase(x); 
        } else {
            ++x; 
        }
    }

    bool found = false;
    for (auto x = m_nodes.begin(); x != m_nodes.end(); ++x) {
        if ((*x)->id == node_id) {
            delete *x;         
            m_nodes.erase(x);  
            found = true;
            break;
        }
    }

    if (!found) {
        throw std::out_of_range("Node was not found!");
    }
}

void Graph::removeEdge(const Edge& edge){
    bool found = false;
    for (auto x = m_edges.begin(); x != m_edges.end(); ++x) {
        if (*x == edge) {
            m_edges.erase(x); 
            found = true;
            break; 
        }
    }

    if (!found) {
        throw std::out_of_range("Edge was not found!");
    }
}

size_t Graph::nodeCount() const{
    return m_nodes.size();
}

size_t Graph::edgeCount() const{
    return m_edges.size();
}

size_t Graph::nodeDegree(size_t node_id) const{
    bool exists = false;
    for (auto node : m_nodes) {
        if (node->id == node_id) { exists = true; break; }
    }
    if (!exists) throw std::out_of_range("This degree does not exist!");

    size_t degree = 0;
    for (const auto& edge : m_edges) {
        if (edge.a == node_id || edge.b == node_id) degree++;
    }
    return degree;
}

size_t Graph::graphDegree() const{
    size_t max_degree = 0;
    for (auto node : m_nodes) {
        size_t degree = nodeDegree(node->id);
        if (degree > max_degree) max_degree = degree;
    }
    return max_degree;
}

void Graph::coloring(){
    for (auto node : m_nodes) {
        node->color = 0;
    }

    for (auto node : m_nodes) {
        std::vector<bool> used_colors(m_nodes.size() + 1, false);

        for (const auto& edge : m_edges) {
            size_t neighbor_id;
            if (edge.a == node->id) neighbor_id = edge.b;
            else if (edge.b == node->id) neighbor_id = edge.a;
            else continue; 

            Node* neighbor = getNode(neighbor_id);
            if (neighbor != nullptr && neighbor->color > 0) {
                used_colors[neighbor->color] = true;
            }
        }

        for (size_t color = 1; color < used_colors.size(); ++color) {
            if (!used_colors[color]) {
                node->color = color;
                break;
            }
        }
    }
}

void Graph::clear() {
    for (auto node : m_nodes) delete node;
    m_nodes.clear();
    m_edges.clear();
}

/*** Konec souboru tdd_code.cpp ***/
