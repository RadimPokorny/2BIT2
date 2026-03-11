/**
 * @file        oi.h
 * @author      Ladislav Mosner, VUT FIT Brno, imosner@fit.vutbr.cz
 * @author      Petr Kleparnik, VUT FIT Brno, ikleparnik@fit.vutbr.cz
 * @author      Kamil Behun, VUT FIT Brno, ibehun@fit.vutbr.cz
 * @author      Petr Šilling, VUT FIT Brno, isilling@fit.vutbr.cz
 * @date        16.03.2025
 *
 * @brief       Deklarace funkci pro zapis a cteni frame_buffer z/do souboru.
 *
 */

#ifndef IO_H
#define IO_H

#include "color.h"

// Funkce pro cteni/zapis do/z souboru

// Nacteni BMP souboru do framebuffer struktury
int loadMyBitmap(const char *filename, RGBA **framebuffer, int *width, int *height);

// Ulozeni BMP souboru z framebuffer struktury
int saveMyBitmap(const char *filename, RGBA **framebuffer, int width, int height);

#endif // OI_H
