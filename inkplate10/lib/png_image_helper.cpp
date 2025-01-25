/**
 **************************************************
 * @file        png_image_helper.cpp
 * @brief       Needed for drawPngFromBuffer function as a workaround until
 *              https://github.com/SolderedElectronics/Inkplate-Arduino-library/pull/210 is merged
 *
 *              This code is released under the GNU Lesser General Public
 *License v3.0: https://www.gnu.org/licenses/lgpl-3.0.en.html Please review the
 *LICENSE file included with this example. If you have any questions about
 *licensing, please contact techsupport@e-radionica.com Distributed as-is; no
 *warranty is given.
 *
 * @authors     Soldered.com, Chris Twomey
 ***************************************************/

#include "libs/pngle/pngle.h"

extern Image *_imagePtrPng;

static bool _pngInvert = 0;
static bool _pngDither = 0;
static int16_t lastY = -1;
static uint16_t _pngX = 0;
static uint16_t _pngY = 0;
static Image::Position _pngPosition = Image::_npos;

uint8_t ditherBuffer[2][E_INK_WIDTH + 20];

/**
 * @brief       pngle_on_buffer_draw
 *
 * @param       pngle_t *pngle
 *              pointer to image
 * @param       uint32_t x
 *              x plane position
 * @param       uint32_t y
 *              y plane position
 * @param       uint32_t w
 *              image width
 * @param       uint32_t h
 *              image height
 * @param       uint8_t rgba[4]
 *              color
 */
void pngle_on_buffer_draw(pngle_t *pngle, uint32_t x, uint32_t y, uint32_t w, uint32_t h, uint8_t rgba[4])
{
    if (_pngPosition != Image::_npos)
    {
        _imagePtrPng->getPointsForPosition(_pngPosition, pngle_get_width(pngle), pngle_get_height(pngle), E_INK_WIDTH,
                                           E_INK_HEIGHT, &_pngX, &_pngY);
        lastY = _pngY;
        _pngPosition = Image::_npos;
    }
    if (rgba[3])
        for (int j = 0; j < h; ++j)
            for (int i = 0; i < w; ++i)
            {
                uint8_t r = rgba[0];
                uint8_t g = rgba[1];
                uint8_t b = rgba[2];

                pngle_ihdr_t *ihdr = pngle_get_ihdr(pngle);

                if (ihdr->depth == 1)
                    r = g = b = (b ? 0xFF : 0);

                uint8_t px = RGB3BIT(r, g, b);

                if (_pngDither)
                {
                    px = _imagePtrPng->ditherGetPixelBmp(RGB8BIT(r, g, b), x + i, y + j, _imagePtrPng->width(), 0);
                    if (_pngInvert)
                        px = 7 - px;
                    if (_imagePtrPng->getDisplayMode() == INKPLATE_1BIT)
                        px = (~px >> 2) & 1;
                }
                _imagePtrPng->drawPixel(_pngX + x + i, _pngY + y + j, px);
            }
    if (lastY != y)
    {
        lastY = y;
        _imagePtrPng->ditherSwap(_imagePtrPng->width());
    }
}

/**
 * @brief       drawPngFromBuffer function draws png image from buffer
 *
 * @param       int32_t len
 *              size of buffer
 * @param       int x
 *              x position for top left image corner
 * @param       int y
 *              y position for top left image corner
 * @param       bool dither
 *              1 if using dither, 0 if not
 * @param       bool invert
 *              1 if using invert, 0 if not
 *
 * @return      1 if drawn successfully, 0 if not
 */
bool drawPngFromBuffer(uint8_t *buf, int32_t len, int x, int y, bool dither, bool invert)
{
    _pngDither = dither;
    _pngInvert = invert;
    lastY = y;

    bool ret = 1;

    if (dither)
        memset(ditherBuffer, 0, sizeof ditherBuffer);

    pngle_t *pngle = pngle_new();
    _pngX = x;
    _pngY = y;
    pngle_set_draw_callback(pngle, pngle_on_buffer_draw);

    if (!buf)
        return 0;

    if (pngle_feed(pngle, buf, len) < 0)
        ret = 0;
    pngle_destroy(pngle);

    free(buf);
    return ret;
}
