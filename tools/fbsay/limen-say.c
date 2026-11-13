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
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/fb.h>

#include <zlib.h>
#include "font.h"

#define PAPER 0xF3F1EC
#define INK   0x1B1813
#define MUTED 0x575144
#define BRASS 0x7A5D18
#define RULE  0xDCD6C9
#define FAINT_C 0x6B6554

static unsigned char *fb;
static struct fb_var_screeninfo vi;
static struct fb_fix_screeninfo fi;

/* Everything is drawn into this RGB buffer first.
 *
 * Writing straight to /dev/fb0 is not reliably visible: MainUI composites
 * through DRM and its plane sits above the fbdev emulation, so our pixels
 * can land somewhere the panel never shows. The vendor's own fbdisplay
 * demonstrably works (it draws the firmware's loading screen), and it takes
 * a PNG. So we render once and can emit either way. */
#define CW 640
#define CH 480
static unsigned char canvas[CW * CH * 3];
static int use_canvas = 0;

static void px(int x, int y, unsigned int rgb)
{
    if (use_canvas) {
        if (x < 0 || y < 0 || x >= CW || y >= CH) return;
        unsigned char *p = canvas + ((size_t)y * CW + x) * 3;
        p[0] = rgb >> 16; p[1] = rgb >> 8; p[2] = rgb;
        return;
    }
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

static void be32(unsigned char *p, unsigned int v)
{ p[0]=v>>24; p[1]=v>>16; p[2]=v>>8; p[3]=v; }

static int write_png(const char *path)
{
    /* filter byte 0 per row, then one zlib stream */
    size_t raw = (size_t)CH * (1 + CW * 3);
    unsigned char *rb = malloc(raw);
    if (!rb) return -1;
    for (int y = 0; y < CH; y++) {
        rb[(size_t)y * (1 + CW * 3)] = 0;
        memcpy(rb + (size_t)y * (1 + CW * 3) + 1, canvas + (size_t)y * CW * 3, CW * 3);
    }
    uLongf clen = compressBound(raw);
    unsigned char *cb = malloc(clen);
    if (!cb || compress2(cb, &clen, rb, raw, 6) != Z_OK) { free(rb); free(cb); return -1; }
    FILE *f = fopen(path, "wb");
    if (!f) { free(rb); free(cb); return -1; }
    const unsigned char sig[8] = {137,80,78,71,13,10,26,10};
    fwrite(sig, 1, 8, f);
    unsigned char ih[13];
    be32(ih, CW); be32(ih + 4, CH);
    ih[8] = 8; ih[9] = 2; ih[10] = 0; ih[11] = 0; ih[12] = 0;
    unsigned char len[4], tag[4];
    be32(len, 13); fwrite(len, 1, 4, f);
    memcpy(tag, "IHDR", 4); fwrite(tag, 1, 4, f); fwrite(ih, 1, 13, f);
    unsigned long c = crc32(crc32(0, tag, 4), ih, 13);
    be32(len, (unsigned)c); fwrite(len, 1, 4, f);
    be32(len, (unsigned)clen); fwrite(len, 1, 4, f);
    memcpy(tag, "IDAT", 4); fwrite(tag, 1, 4, f); fwrite(cb, 1, clen, f);
    c = crc32(crc32(0, tag, 4), cb, clen);
    be32(len, (unsigned)c); fwrite(len, 1, 4, f);
    be32(len, 0); fwrite(len, 1, 4, f);
    memcpy(tag, "IEND", 4); fwrite(tag, 1, 4, f);
    c = crc32(0, tag, 4); be32(len, (unsigned)c); fwrite(len, 1, 4, f);
    fclose(f); free(rb); free(cb);
    return 0;
}

int main(int argc, char **argv)
{
    const char *title = NULL;
    const char *footer = NULL;
    const char *png = NULL;
    for (int i = 1; i < argc; i++)
        if (!strcmp(argv[i], "--png") && i + 1 < argc) { png = argv[i + 1]; use_canvas = 1; }

    int fd = -1; size_t len = 0;
    if (use_canvas) {
        vi.xres = CW; vi.yres = CH; vi.bits_per_pixel = 24;
        vi.red.offset = 0; vi.green.offset = 8; vi.blue.offset = 16;
        vi.transp.length = 0; vi.xoffset = vi.yoffset = 0;
        fi.line_length = CW * 3;
    } else {
        fd = open("/dev/fb0", O_RDWR);
        if (fd < 0) { perror("open /dev/fb0"); return 1; }
        if (ioctl(fd, FBIOGET_VSCREENINFO, &vi) || ioctl(fd, FBIOGET_FSCREENINFO, &fi)) {
            perror("ioctl"); return 1;
        }
        len = (size_t)fi.line_length * (vi.yres_virtual ? vi.yres_virtual : vi.yres);
        fb = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        if (fb == MAP_FAILED) { perror("mmap"); return 1; }
    }

    /* collect the lines */
    char *lines[64]; int n = 0;
    for (int i = 1; i < argc && n < 60; i++) {
        if (!strcmp(argv[i], "--title") && i + 1 < argc) { title = argv[++i]; continue; }
        if (!strcmp(argv[i], "--footer") && i + 1 < argc) { footer = argv[++i]; continue; }
        if (!strcmp(argv[i], "--png")    && i + 1 < argc) { i++; continue; }
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

    /* Fit the content to the panel instead of running off the bottom.
     * The first build used a fixed 6px gap and a Status screen with 13 lines
     * simply lost its last three. Compute the step from how many lines there
     * actually are, and drop the title to single height when it is tight. */
    int head = 26;
    int title_scale = 2;
    int y = head;
    int avail;
    for (;;) {
        int head_h = title ? (GH * title_scale + 10 + 18 + 2) : 0;
        /* the footer is a rule 12px above a line sitting 8px off the bottom,
         * so the zone it needs is GH + 8 + 12 + 2 plus breathing room. The
         * first value reserved only GH + 14 and the last body line was drawn
         * straight through the divider. */
        int foot_h = footer ? (GH + 30) : 0;
        avail = (int)vi.yres - head - head_h - foot_h - 6;
        if (n == 0 || avail / n >= GH + 1 || title_scale == 1) break;
        title_scale = 1;                /* reclaim the title's second row */
    }
    int step = (n > 0) ? avail / n : GH + 6;
    if (step > GH + 8) step = GH + 8;   /* do not sprawl when there is room */
    if (step < GH) step = GH;           /* never overlap glyphs; GH is tight but legal */

    if (title) {
        text(24, y, title, INK, title_scale);
        y += GH * title_scale + 10;
        fill(24, y, vi.xres - 48, 2, RULE);
        y += 18;
    }
    for (int i = 0; i < n; i++) {
        /* a line beginning '>' is emphasised in gold */
        const char *s = lines[i];
        unsigned int col = MUTED;
        if (s[0] == '>') { col = BRASS; s++; while (*s == ' ') s++; }
        text(24, y, s, col, 1);
        y += step;
        if (y > (int)vi.yres - GH) break;
    }
    if (footer) {
        int fy = (int)vi.yres - GH - 8;
        fill(24, fy - 12, vi.xres - 48, 2, RULE);
        const char *s2 = footer;
        unsigned int fc = FAINT_C;
        if (s2[0] == '>') { fc = BRASS; s2++; while (*s2 == ' ') s2++; }
        text(24, fy, s2, fc, 1);
    }
    if (use_canvas) {
        if (write_png(png) != 0) { fprintf(stderr, "png write failed\n"); return 1; }
    } else {
        munmap(fb, len);
        close(fd);
    }
    return 0;
}
