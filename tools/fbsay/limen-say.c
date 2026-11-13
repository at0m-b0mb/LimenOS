/* ==========================================================================
 * limen-say - draw a status screen on the Miyoo Flip framebuffer.
 *
 * The stock firmware can only put a PNG on screen (fbdisplay), which is no
 * use for live values like an IP address or a temperature. There is no
 * framebuffer console in this kernel either (CONFIG_FRAMEBUFFER_CONSOLE is
 * unset), so there is nothing to print to. This draws directly to /dev/fb0.
 *
 * Statically linked on purpose: the device runs glibc 2.36 and the build
 * container is newer, so a dynamic binary would not load.
 *
 *   limen-say --title "LimenOS" "line one" "line two"
 *   somecommand | limen-say --title "Status" -
 *
 * Colours are the project palette: warm paper, ink, one gold rule.
 * ========================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/fb.h>

#include "font.h"

#define PAPER 0xF3F1EC
#define INK   0x1B1813
#define MUTED 0x575144
#define BRASS 0x7A5D18
#define RULE  0xDCD6C9

static unsigned char *fb;
static struct fb_var_screeninfo vi;
static struct fb_fix_screeninfo fi;

static void px(int x, int y, unsigned int rgb)
{
    if (x < 0 || y < 0 || x >= (int)vi.xres || y >= (int)vi.yres) return;
    unsigned char r = rgb >> 16, g = rgb >> 8, b = rgb;
    unsigned char *p = fb + (y + vi.yoffset) * fi.line_length
                          + (x + vi.xoffset) * (vi.bits_per_pixel / 8);
    if (vi.bits_per_pixel == 32 || vi.bits_per_pixel == 24) {
        p[vi.red.offset / 8]   = r;
        p[vi.green.offset / 8] = g;
        p[vi.blue.offset / 8]  = b;
        if (vi.bits_per_pixel == 32 && vi.transp.length) p[vi.transp.offset / 8] = 0xff;
    } else if (vi.bits_per_pixel == 16) {
        unsigned short v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
        *(unsigned short *)p = v;
    }
}

static void fill(int x0, int y0, int w, int h, unsigned int rgb)
{
    for (int y = y0; y < y0 + h; y++)
        for (int x = x0; x < x0 + w; x++) px(x, y, rgb);
}

/* draw one glyph, scaled by integer factor s */
static void glyph(int x, int y, char c, unsigned int rgb, int s)
{
    /* control characters are not glyphs: draw nothing rather than a '?',
     * which is what made a stray newline show up mid-line on the device */
    if (c < 32 || c > 126) return;
    const unsigned short *g = FONT[c - 32];
    for (int row = 0; row < GH; row++)
        for (int col = 0; col < GW; col++)
            if (g[row] & (1 << (GW - 1 - col)))
                fill(x + col * s, y + row * s, s, s, rgb);
}

static void text(int x, int y, const char *s, unsigned int rgb, int sc)
{
    for (const char *p = s; *p; p++, x += GW * sc) glyph(x, y, *p, rgb, sc);
}

int main(int argc, char **argv)
{
    const char *title = NULL;
    int fd = open("/dev/fb0", O_RDWR);
    if (fd < 0) { perror("open /dev/fb0"); return 1; }
    if (ioctl(fd, FBIOGET_VSCREENINFO, &vi) || ioctl(fd, FBIOGET_FSCREENINFO, &fi)) {
        perror("ioctl"); return 1;
    }
    size_t len = (size_t)fi.line_length * (vi.yres_virtual ? vi.yres_virtual : vi.yres);
    fb = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (fb == MAP_FAILED) { perror("mmap"); return 1; }

    /* collect the lines */
    char *lines[64]; int n = 0;
    for (int i = 1; i < argc && n < 60; i++) {
        if (!strcmp(argv[i], "--title") && i + 1 < argc) { title = argv[++i]; continue; }
        if (!strcmp(argv[i], "-")) {
            static char buf[64][128];
            while (n < 60 && fgets(buf[n], sizeof buf[0], stdin)) {
                buf[n][strcspn(buf[n], "\r\n")] = 0;
                lines[n] = buf[n]; n++;
            }
            continue;
        }
        lines[n++] = argv[i];
    }

    /* paint */
    fill(0, 0, vi.xres, vi.yres, PAPER);
    fill(0, 0, vi.xres, 3, BRASS);

    int y = 26;
    if (title) {
        text(24, y, title, INK, 2);
        y += GH * 2 + 10;
        fill(24, y, vi.xres - 48, 2, RULE);
        y += 18;
    }
    for (int i = 0; i < n; i++) {
        /* a line beginning '>' is emphasised in gold */
        const char *s = lines[i];
        unsigned int col = MUTED;
        if (s[0] == '>') { col = BRASS; s++; while (*s == ' ') s++; }
        text(24, y, s, col, 1);
        y += GH + 6;
        if (y > (int)vi.yres - GH) break;
    }
    munmap(fb, len);
    close(fd);
    return 0;
}
