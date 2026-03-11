/**
 * @file        student.h
 * @author      Ladislav Mosner, VUT FIT Brno, imosner@fit.vutbr.cz
 * @author      Petr Kleparnik, VUT FIT Brno, ikleparnik@fit.vutbr.cz
 * @author      Kamil Behun, VUT FIT Brno, ibehun@fit.vutbr.cz
 * @author      Petr Šilling, VUT FIT Brno, isilling@fit.vutbr.cz
 * @date        16.03.2025
 *
 * @brief       Deklarace funkci studentu.
 *
 */

#ifndef STUDENT_H
#define STUDENT_H

#ifdef __linux__
    #include <limits.h>
#endif

#include <vector>
#include <time.h>
#include <stdio.h>

#include "color.h"

void putPixel(int x, int y, RGBA color);

RGBA getPixel(int x, int y);

void drawTriangle(const Point &v1, const Point &v2, const Point &v3, const RGBA &edgeColor);

#endif // STUDENT_H
