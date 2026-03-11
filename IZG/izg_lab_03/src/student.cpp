/**
 * @file        student.cpp
 * @author      Ladislav Mosner, VUT FIT Brno, imosner@fit.vutbr.cz
 * @author      Petr Kleparnik, VUT FIT Brno, ikleparnik@fit.vutbr.cz
 * @author      Kamil Behun, VUT FIT Brno, ibehun@fit.vutbr.cz
 * @author      Petr Šilling, VUT FIT Brno, isilling@fit.vutbr.cz
 * @date        16.03.2025
 *
 * @brief       Definice funkci studentu: SOUBOR S BODOVANYMI UKOLY
 *
 */

#include "base.h"
#include "student.h"
#include "globals.h"
#include <math.h>

/**
 * @brief Vraci barvu pixelu z pozice [x, y]
 * @param[in] x X souradnice pixelu
 * @param[in] y Y souradnice pixelu
 * @return Barva pixelu na pozici [x, y] ve formatu RGBA
 */
RGBA getPixel(int x, int y)
{
    if (x >= width || y >= height || x < 0 || y < 0) {
        IZG_ERROR("Pristup do framebufferu mimo hranice okna\n");
    }
    return framebuffer[y * width + x];
}

/**
 * @brief Nastavi barvu pixelu na pozici [x, y]
 * @param[in] x X souradnice pixelu
 * @param[in] y Y souradnice pixelu
 * @param[in] color Barva pixelu ve formatu RGBA
 */
void putPixel(int x, int y, RGBA color)
{
    if (x >= width || y >= height || x < 0 || y < 0) {
        IZG_ERROR("Pristup do framebufferu mimo hranice okna\n");
    }
    framebuffer[y * width + x] = color;
}

/**
 * @brief Vykresli usecku se souradnicemi [x1, y1] a [x2, y2]
 * @param[in] x1 X souradnice 1. bodu usecky
 * @param[in] y1 Y souradnice 1. bodu usecky
 * @param[in] x2 X souradnice 2. bodu usecky
 * @param[in] y2 Y souradnice 2. bodu usecky
 * @param[in] color Barva pixelu usecky ve formatu RGBA
 * @param[in] arrow Priznak pro vykresleni sipky (orientace hrany)
 */
void drawLine(int x1, int y1, int x2, int y2, RGBA color, bool arrow = false)
{
    if (arrow) {
        // Sipka na konci hrany
        double vx1 = x2 - x1;
        double vy1 = y2 - y1;
        double length = sqrt(vx1 * vx1 + vy1 * vy1);
        double vx1N = vx1 / length;
        double vy1N = vy1 / length;
        double vx1NN = -vy1N;
        double vy1NN = vx1N;
        int w = 3;
        int h = 10;
        int xT = (int) (x2 + w * vx1NN - h * vx1N);
        int yT = (int) (y2 + w * vy1NN - h * vy1N);
        int xB = (int) (x2 - w * vx1NN - h * vx1N);
        int yB = (int) (y2 - w * vy1NN - h * vy1N);
        drawTriangle(Point(x2, y2), Point(xT, yT), Point(xB, yB), color);
    }

    bool steep = abs(y2 - y1) > abs(x2 - x1);

    if (steep) {
        SWAP(x1, y1);
        SWAP(x2, y2);
    }

    if (x1 > x2) {
        SWAP(x1, x2);
        SWAP(y1, y2);
    }

    const int dx = x2 - x1, dy = abs(y2 - y1);
    const int P1 = 2 * dy, P2 = P1 - 2 * dx;
    int P = 2 * dy - dx;
    int y = y1;
    int ystep = 1;
    if (y1 > y2) ystep = -1;

    for (int x = x1; x <= x2; x++) {
        if (steep) {
            if (y >= 0 && y < width && x >= 0 && x < height) {
                putPixel(y, x, color);
            }
        } else {
            if (x >= 0 && x < width && y >= 0 && y < height) {
                putPixel(x, y, color);
            }
        }

        if (P >= 0) {
            P += P2;
            y += ystep;
        } else {
            P += P1;
        }
    }
}

/**
 * @brief Vyplni a vykresli trojuhelnik s interpolovanymi barvami ve vrcholech
 * @param[in] v1 Prvni bod trojuhelniku
 * @param[in] v2 Druhy bod trojuhelniku
 * @param[in] v3 Treti bod trojuhelniku
 * @param[in] edgeColor Barva hran trojuhelniku
 *
 * FUNKCE S BODOVANYMI UKOLY
 */
void drawTriangle(const Point& v1, const Point& v2, const Point& v3, const RGBA& edgeColor)
{
    // Nalezeni obalky (minX, maxX), (minY, maxY) trojuhleniku.

    //////// DOPLNIME SPOLECNE /////////
    int minX = v1.x;
    int minY = v1.y;

    int maxX = v1.x;
    int maxY = v1.y;


    // Oriznuti obalky (minX, maxX, minY, maxY) trojuhleniku podle rozmeru okna.
    minX = MAX(0, minX);
    minY = MAX(0, minY);
    maxX = MIN(width - 1, maxX);
    maxY = MIN(height - 1, maxY);

    // Spocitani parametru hranove funkce (deltaX, deltaY) pro kazdou hranu.
    // Hodnoty deltaX, deltaY jsou souradnicemi vektoru, ktery ma pocatek
    // v prvnim vrcholu hrany a konec ve druhem vrcholu hrany.

    //////// DOPLNIME SPOLECNE /////////


    // Barvy ve vrcholech.
    RGBA v1Color = COLOR_YELLOW;
    RGBA v2Color = COLOR_CYAN;
    RGBA v3Color = COLOR_MAGENTA;

    // Vypocet obsahu trojuhelniku pomoci vektoroveho soucinu hran z prvniho
    // vrcholu.

    //////// DOPLNIME SPOLECNE /////////


    // Vyplnovani: Cyklus pres vsechny body (x, y) v obdelniku (minX, minY), (maxX, maxY).
    // Pro aktualizaci hodnot hranove funkce v bode P (x +/- 1, y) nebo P (x, y +/- 1)
    // vyuzijte hodnoty hranove funkce E (x, y) z bodu P (x, y).

    for (int y = minY; y <= maxY; y++) {

        // Vypocet prvotnich hodnot hranovych funkci (edgeF12, edgeF23, edgeF31)
        // pro prvni bod na radku.

        //////// DOPLNIME SPOLECNE /////////

        for (int x = minX; x <= maxX; x++) {
            // Kontrola nalezitosti pixelu trojuhelniku pomoci hranovych funkci.

            //////// DOPLNIME SPOLECNE /////////
            if (true) {
                // Vypocet obsahu (area12, area23, area31) dilcich casti hlavniho
                // trojuhelniku pro vypocet barycentrickych souradnic. Vyuzijte
                // vypocet pomoci vektoroveho soucinu.

                //////// BODOVANY UKOL /////////

                // Vypocet obsahu (area12, area23, area31) pomoci hranovych funkci.
                // Predchozi vypocet pomoci vektoroveho soucinu nemazte, pouze upravte
                // hodnoty. Pouzijte ve vztahu primo hodnoty hranovych funkci.

                //////// BODOVANY UKOL /////////

                // Vypocet barycentrickych souradnic (lambda1, lambda2, lambda3).

                //////// BODOVANY UKOL /////////

                // Interpolace barev ve vrcholech. Vypoctene vahy aplikujte na kazdy kanal
                // (R, G, B) zvlast.

                //////// BODOVANY UKOL /////////
                float r = v1Color.red;
                float g = v1Color.green;
                float b = v1Color.blue;


                // Konstrukce interpolovane barvy z vypoctenych hodnot.
                RGBA interpolated_color = makeColor(r, g, b);

                // Vykresleni obarveneho pixelu.
                putPixel(x, y, interpolated_color);
            }

            // Aktualizace hodnot hranovych funkci pri posunu na radku.

            //////// DOPLNIME SPOLECNE /////////
        }
    }

    // Prekresleni hranic trojuhelniku barvou edgeColor.
    drawLine(v1.x, v1.y, v2.x, v2.y, edgeColor);
    drawLine(v2.x, v2.y, v3.x, v3.y, edgeColor);
    drawLine(v3.x, v3.y, v1.x, v1.y, edgeColor);
}
