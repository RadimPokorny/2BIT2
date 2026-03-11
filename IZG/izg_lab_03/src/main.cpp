/**
 * @file        main.cpp
 * @author      Ladislav Mosner, VUT FIT Brno, imosner@fit.vutbr.cz
 * @author      Petr Kleparnik, VUT FIT Brno, ikleparnik@fit.vutbr.cz
 * @author      Kamil Behun, VUT FIT Brno, ibehun@fit.vutbr.cz
 * @author      Petr Šilling, VUT FIT Brno, isilling@fit.vutbr.cz
 * @date        16.03.2025
 *
 * @brief       Zaklady pocitacove grafiky (IZG), 3. cviceni.
 *
 *      Ovladani programu:
 *          "Leva mys"      - Prida novy bod trojuhelniku
 *          "C"             - Vymaze frame buffer
 *          "S"             - Ulozi aktualni obraz do out.bmp
 *          "Esc"           - Ukonci program
 *
 */

#ifdef _WIN32
#include <windows.h>
#endif

#include "color.h"
#include "student.h"
#include "io.h"
#include "globals.h"

#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <iostream>

// Globalni konstanty a promenne

// Titulek hlavniho okna
const char *PROGRAM_TITLE = "IZG/2025 Lab 03";

// Vychozi velikost okna
const int DEFAULT_WIDTH = 800;
const int DEFAULT_HEIGHT = 600;

// Kreslici buffer knihovny SDL
SDL_Surface *screen = 0;

// Kreslici buffer IZG cvičení
RGBA *framebuffer = 0;

// Pomocna promenna pro ukonceni aplikace
int quit = 0;

// Sirka a vyska okna
int width = 800;
int height = 600;

// Nazvy i/o souboru
char *outputImageName = "data/out.bmp";

// Vychozi barva hrany
RGBA edgeColor = COLOR_WHITE;

int background = 0;

// Zasobnik bodu
SeedStack points;

// Stav pouziti algoritmu
bool isOld = false;
int pointCount = 0;

/**
 * @brief Vytvori 1D pole bodu (typu Point) z 2D pole
 * @param[in] points Vstupni 2D pole bodu
 * @param[in] length Delka pole bodu
 * @return Vraci pole bodu typu Point
 */
Point *makeSeedStack(const int points[][2], int length) {
    Point *s = new Point[(unsigned int) length];
    for (int i = 0; i < length; i++) {
        s[i] = Point(points[i][0], points[i][1]);
    }
    return s;
}

/**
 * @brief Zkontroluje orientaci vektoru v poli a pripadne opravi na clockwise
 * @param[in,out] array Pole bodu polygonu
 * @param[in] length Delka pole bodu
 */
void clockwiseOrientatedArray(Point *array, int length) {
    int accum = 0;

    for (int i = 0; i < length; i++) {
        Point p1 = array[i];
        Point p2 = array[(i + 1) % length];
        accum += (p2.x - p1.x) * (p2.y + p1.y);
    }

    if (accum >= 0) {
        Point temp;
        for (int i = 0; i < length / 2; ++i) {
            temp = array[length - i - 1];
            array[length - i - 1] = array[i];
            array[i] = temp;
        }
    }
}

/**
 * @brief Spusti jeden z testu
 * @param[in] test Cislo testu
 */
void runTest(int test) {
    Point *points(0);

    switch (test) {
        // 1) Try to create a triangle
        case 1: {
            const int points1[3][2] = {{30, 88}, {182, 22}, {175, 128}};
            points = makeSeedStack(points1, 3);
            drawTriangle((const Point) points[0], (const Point) points[1], (const Point) points[2], edgeColor);
            delete[] points;
            break;
        }
        // 2) Try to create triangle out of view
        case 2: {
            const int points2[3][2] = {{256, 121}, {250, -10}, {900, 200}};
            points = makeSeedStack(points2, 3);
            drawTriangle((const Point) points[0], (const Point) points[1], (const Point) points[2], edgeColor);
            delete[] points;
            break;
        }
        // 3) Try to create triangle with zero length side
        case 3: {
            const int points3[3][2] = {{195, 150}, {195, 180}, {195, 200}};
            points = makeSeedStack(points3, 3);
            drawTriangle((const Point)points[0], (const Point)points[1], (const Point)points[2], edgeColor);
            delete[] points;
            break;
        }
    }
}

/**
 * @brief Copy bitmap
 * @param[in] srcColors Source color pixels
 * @param[out] dstColors Destination color pixels
 * @param[in] x Destination position x
 * @param[in] y Destination position y
 * @param[in] srcWidth Source width
 * @param[in] srcHeight Source height
 * @param[in] dstWidth Destination width
 */
void copyBuffer(RGBA *srcColors, RGBA *dstColors, int srcWidth, int srcHeight, int dstX, int dstY, int dstWidth) {
    // Prepocitana pozice v cilovem bufferu;
    RGBA *dstColorNew(dstColors + dstX + dstY * dstWidth);

    // Castecna kopie obsahu frame bufferu
    for (int i = 0; i < srcHeight; i++) {
        memcpy(dstColorNew + i * dstWidth, srcColors + i * srcWidth, srcWidth * sizeof(RGBA));
    }
}

/**
 * @brief Prekresleni obsahu okna programu
 */
void onDraw(void) {
    // Test existence frame bufferu a obrazove pameti
    IZG_ASSERT(framebuffer && screen);

    // Test typu pixelu
    IZG_ASSERT(screen->format->BytesPerPixel == 4);

    // Kopie bufferu do obrazove pameti
    SDL_LockSurface(screen);

    // Test, pokud kopirujeme rozdilnou velikost framebufferu a rozdilne pameti, musime pamet prealokovat
    if (width != screen->w || height != screen->h) {
        SDL_SetVideoMode(width, height, 32, SDL_SWSURFACE);
        /*SDL_FreeSurface(screen);
        if (!(screen = SDL_SetVideoMode(width, height, 32, SDL_SWSURFACE|SDL_ANYFORMAT)))
        {
        IZG_ERROR("Cannot realocate screen buffer");
        SDL_Quit();
        }*/
    }

    MEMCOPY(screen->pixels, framebuffer, sizeof(RGBA) * width * height);
    SDL_UnlockSurface(screen);

    // Vymena zobrazovaneho a zapisovaneho bufferu
    SDL_Flip(screen);
}

/**
 * @brief Funkce reagujici na stisknuti klavesnice
 * @param[in] key Udalost klavesnice
 */
void onKeyboard(SDL_KeyboardEvent *key) {
    // Test existence rendereru
    IZG_ASSERT(framebuffer);

    // Vetveni podle stisknute klavesy
    switch (key->keysym.sym) {
        case SDLK_c:
            memset(framebuffer, background, width * height * sizeof(RGBA));
            break;
        // Testy, ktere lze pouzit pro kontrolu ukolu.
        case SDLK_1:
        case SDLK_2:
        case SDLK_3:
            runTest(key->keysym.sym - SDLK_1 + 1);
            break;
        // Ukonceni programu - klavesa Esc
        case SDLK_ESCAPE:
            quit = 1;
            break;
        case SDLK_s:
            // Stisknuti S tlacitka ulozi obrazek
            if (saveMyBitmap(outputImageName, &framebuffer, width, height))
                IZG_INFO("File successfully saved\n")
            else
                IZG_ERROR("Error in saving the file.\n");
            break;
        default:
            break;
    }
}

/**
 * @brief Funkce reagujici na zmacknuti tlacitka mysi
 * @param mouse Udalost mysi
 */
void onMouseDown(SDL_MouseButtonEvent *mouse) {
    if (mouse->button == SDL_BUTTON_LEFT) {
        putPixel(mouse->x, mouse->y, COLOR_GREEN);
        points.push_back(Point(mouse->x, mouse->y));
        pointCount++;
        isOld = true;
        if (pointCount >= 3) {
            Point *pointsTmp;
            STACK_TO_ARRAY(points, pointsTmp);
            // Fill polygon
            clockwiseOrientatedArray(pointsTmp, 3);
            drawTriangle(pointsTmp[0], pointsTmp[1], pointsTmp[2], edgeColor);
            delete[] pointsTmp;
            points.clear();
            isOld = false;
            pointCount = 0;
        }
    }
}

/**
 * @brief Tiskne napovedu
 */
void printHelpText() {
    IZG_INFO("Application loaded - IZG LAB 03 - 2D area filling. Controls:\n\n"
        "Left mouse click:\n"
        "    Adds new point to triangle\n\n"
        "C key:\n"
        "    Clears framebuffer\n\n"
        "S key:\n"
        "    Saves current view into out.bmp image\n"
        "        (depends on GetPixel function)\n\n"
        "1..3 keys:\n"
        "    Run tests for Pineda's algorithm\n\n"
        "\n\n")
}

/**
 * @brief Hlavni funkce programu
 * @param argc Pocet vstupnich parametru
 * @param argv Pole vstupnich parametru
 * @return
 */
int main(int argc, char *argv[]) {
    SDL_Event event;

    // Inicializace SDL knihovny
    if (SDL_Init(SDL_INIT_VIDEO) == -1) {
        IZG_SDL_ERROR("Could not initialize SDL library");
    }

    // Nastaveni okna
    SDL_WM_SetCaption(PROGRAM_TITLE, 0);

    // Alokace frame bufferu (okno + SW zapisovaci buffer)
    if (!(screen = SDL_SetVideoMode(width, height, 32, SDL_SWSURFACE))) {
        SDL_Quit();
        return 1;
    }
    if (!(framebuffer = (RGBA *) malloc(sizeof(RGBA) * width * height))) {
        SDL_Quit();
        return 1;
    }

    // Clear framebuffer
    memset(framebuffer, background, width * height * sizeof(RGBA));

    printHelpText();

    // Kreslime, dokud nenarazime na SDL_QUIT event
    while (!quit) {
        // Reakce na udalost
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
                // Udalost klavesnice
                case SDL_KEYDOWN:
                    onKeyboard(&event.key);
                    break;

                    // Udalost mysi
                case SDL_MOUSEBUTTONDOWN:
                    onMouseDown(&event.button);
                    break;

                    // SDL_QUIT event
                case SDL_QUIT:
                    quit = 1;
                    break;

                default:
                    break;
            }
        }

        // Provedeme preklopeni zapisovaciho framebufferu na obrazovku
        onDraw();
    }

    // Uvolneni pameti
    SDL_FreeSurface(screen);
    free(framebuffer);
    SDL_Quit();

    IZG_INFO("Bye bye....\n\n");
    return 0;
}
