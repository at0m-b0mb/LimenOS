/* ==========================================================================
 * limen-shell - a terminal for the Miyoo Flip, driven entirely by the D-pad.
 *
 * The Flip has no keyboard and this kernel has no framebuffer console
 * (CONFIG_FRAMEBUFFER_CONSOLE is unset), so there is nothing to type into and
 * nothing to print to. This draws its own screen on /dev/fb0 and its own
 * keyboard, reads the gamepad from /dev/input/event5, and runs what you type.
 *
 * It draws straight to the framebuffer rather than through fbdisplay because
 * it has to repaint on every keypress. That works here: the launcher EXITS
 * before running an app, so nothing is composing over the framebuffer while
 * this is on screen.
 *
 *   D-pad      move around the keyboard
 *   A          type the highlighted key
 *   B          backspace
 *   X          switch letters / symbols
 *   Y          space
 *   START      run the command
 *   L / R      scroll the output
 *   SELECT     quit
 *
 * Statically linked: the device is glibc 2.36 and the build container is
 * newer, so a dynamic binary would not load.
 * ========================================================================== */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
#include <linux/input.h>

#include "font.h"

/* house palette, dark: the launcher's own themes are all dark and so is ours */
#define BG      0x000000
#define SURFACE 0x131312
#define INK     0xF3F0E9
#define MUTED   0xA29C91
#define FAINT   0x8C877C
#define RULE    0x2B2B28
#define RULE2   0x3D3C38
#define BRASS   0xD9B75C
#define SHINE   0xF1C84B
#define BAD     0xEE8B82

static unsigned char *fb;
static struct fb_var_screeninfo vi;
static struct fb_fix_screeninfo fi;
static int W, H;

/* ------------------------------------------------------------------ paint */
static void px(int x, int y, unsigned int rgb)
{
    if (x < 0 || y < 0 || x >= W || y >= H) return;
    unsigned char *p = fb + (size_t)(y + vi.yoffset) * fi.line_length
                          + (size_t)(x + vi.xoffset) * (vi.bits_per_pixel / 8);
    unsigned char r = rgb >> 16, g = rgb >> 8, b = rgb;
    if (vi.bits_per_pixel >= 24) {
        p[vi.red.offset / 8] = r; p[vi.green.offset / 8] = g; p[vi.blue.offset / 8] = b;
        if (vi.bits_per_pixel == 32 && vi.transp.length) p[vi.transp.offset / 8] = 0xff;
    } else {
        *(unsigned short *)p = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
    }
}

static void fill(int x, int y, int w, int h, unsigned int c)
{ for (int j = y; j < y + h; j++) for (int i = x; i < x + w; i++) px(i, j, c); }

static void frame(int x, int y, int w, int h, unsigned int c, int t)
{
    fill(x, y, w, t, c); fill(x, y + h - t, w, t, c);
    fill(x, y, t, h, c); fill(x + w - t, y, t, h, c);
}

static void glyph(int x, int y, char ch, unsigned int c, int s)
{
    if (ch < 32 || ch > 126) return;
    const unsigned short *g = FONT[ch - 32];
    for (int r = 0; r < GH; r++)
        for (int col = 0; col < GW; col++)
            if (g[r] & (1 << (GW - 1 - col))) fill(x + col * s, y + r * s, s, s, c);
}

static void text(int x, int y, const char *s, unsigned int c, int sc)
{ for (; *s; s++, x += GW * sc) glyph(x, y, *s, c, sc); }

static int textw(const char *s, int sc) { return (int)strlen(s) * GW * sc; }

/* ------------------------------------------------------------- keyboard */
#define KROWS 5
#define KCOLS 10
static const char *LOWER[KROWS] = {
    "1234567890", "qwertyuiop", "asdfghjkl-", "zxcvbnm.,/", "~|>'\"$*&;:"
};
static const char *UPPER[KROWS] = {
    "!@#$%^&*()", "QWERTYUIOP", "ASDFGHJKL_", "ZXCVBNM<>?", "`\\=+[]{}()"
};
static int shift = 0, kx = 0, ky = 1;

/* --------------------------------------------------------------- output */
#define MAXLINES 400
#define MAXCOL   76
static char out[MAXLINES][MAXCOL + 1];
static int nout = 0, scroll = 0;

static void outclear(void) { nout = 0; scroll = 0; }

static void outadd(const char *s)
{
    while (*s) {
        if (nout >= MAXLINES) {                 /* keep the tail, drop the head */
            memmove(out[0], out[1], sizeof(out) - sizeof(out[0]));
            nout = MAXLINES - 1;
        }
        int i = 0;
        while (*s && *s != '\n' && i < MAXCOL) {
            out[nout][i++] = (*s == '\t') ? ' ' : *s;
            s++;
        }
        out[nout][i] = 0; nout++;
        while (*s && *s != '\n') s++;           /* drop the overflow */
        if (*s == '\n') s++;
    }
}

static void run(const char *cmd)
{
    outclear();
    /* the parameter shadows the global cmd[], so sizeof here was the
     * pointer size, not the buffer; spell the capacity out */
    char head[300];
    snprintf(head, sizeof head, "$ %s", cmd);
    outadd(head); outadd("");
    FILE *p = popen(cmd, "r");
    if (!p) { outadd("could not start a shell"); return; }
    char line[1024];
    while (fgets(line, sizeof line, p)) outadd(line);
    int rc = pclose(p);
    char tail[64];
    snprintf(tail, sizeof tail, "[exit %d]", rc == -1 ? -1 : (rc >> 8) & 0xff);
    outadd(""); outadd(tail);
    /* show the end, which is where the answer usually is */
    int rows = 7;
    scroll = nout > rows ? nout - rows : 0;
}

/* ----------------------------------------------------------------- draw */
static char cmd[256];
static int clen = 0;

static void draw(void)
{
    fill(0, 0, W, H, BG);
    fill(0, 0, W, 3, BRASS);

    text(14, 12, "LimenOS Shell", INK, 1);
    text(W - 14 - textw("SELECT quit", 1), 12, "SELECT quit", FAINT, 1);
    fill(14, 44, W - 28, 1, RULE);

    /* the command line */
    int cy = 54;
    fill(14, cy, W - 28, GH + 12, SURFACE);
    frame(14, cy, W - 28, GH + 12, RULE2, 1);
    text(22, cy + 6, "$", BRASS, 1);
    int vis = (W - 70) / GW;                    /* scroll the tail into view */
    const char *show = clen > vis ? cmd + clen - vis : cmd;
    text(22 + GW * 2, cy + 6, show, INK, 1);
    fill(22 + GW * 2 + textw(show, 1), cy + 6, GW, GH, BRASS);   /* cursor */

    /* output */
    int oy = cy + GH + 20;
    int rows = 7;
    fill(14, oy, W - 28, rows * (GH + 2) + 10, SURFACE);
    frame(14, oy, W - 28, rows * (GH + 2) + 10, RULE, 1);
    for (int i = 0; i < rows; i++) {
        int idx = scroll + i;
        if (idx >= nout) break;
        unsigned int c = MUTED;
        if (out[idx][0] == '$') c = BRASS;
        if (strstr(out[idx], "[exit 0]")) c = INK;
        else if (strstr(out[idx], "[exit ")) c = BAD;
        text(22, oy + 6 + i * (GH + 2), out[idx], c, 1);
    }
    if (nout > rows) {
        char pos[48];
        snprintf(pos, sizeof pos, "%d-%d/%d", scroll + 1,
                 scroll + rows > nout ? nout : scroll + rows, nout);
        text(W - 20 - textw(pos, 1), oy - GH - 4, pos, FAINT, 1);
    }

    /* keyboard */
    int kw = 60, kh = 32, gap = 2;
    int kxo = (W - (KCOLS * (kw + gap) - gap)) / 2;
    int kyo = H - (KROWS * (kh + gap) - gap) - 34;
    for (int r = 0; r < KROWS; r++) {
        for (int c = 0; c < KCOLS; c++) {
            int x = kxo + c * (kw + gap), y = kyo + r * (kh + gap);
            int on = (r == ky && c == kx);
            char ch = (shift ? UPPER : LOWER)[r][c];
            fill(x, y, kw, kh, on ? BRASS : SURFACE);
            frame(x, y, kw, kh, on ? SHINE : RULE2, 1);
            char s[2] = { ch, 0 };
            text(x + (kw - GW) / 2, y + (kh - GH) / 2, s, on ? BG : INK, 1);
        }
    }

    /* hints */
    const char *h = shift ? "A type   B del   X abc   Y space   START run   L/R scroll"
                          : "A type   B del   X SYM   Y space   START run   L/R scroll";
    text((W - textw(h, 1)) / 2, H - 24, h, FAINT, 1);
}

/* ---------------------------------------------------------------- input */
static void typech(char c)
{ if (clen < (int)sizeof cmd - 1) { cmd[clen++] = c; cmd[clen] = 0; } }

int main(void)
{
    int fd = open("/dev/fb0", O_RDWR);
    if (fd < 0) { perror("fb0"); return 1; }
    if (ioctl(fd, FBIOGET_VSCREENINFO, &vi) || ioctl(fd, FBIOGET_FSCREENINFO, &fi)) {
        perror("ioctl"); return 1; }
    W = vi.xres; H = vi.yres;
    size_t len = (size_t)fi.line_length * (vi.yres_virtual ? vi.yres_virtual : vi.yres);
    fb = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (fb == MAP_FAILED) { perror("mmap"); return 1; }

    int in = open("/dev/input/event5", O_RDONLY);
    if (in < 0) in = open("/dev/input/event0", O_RDONLY);
    if (in < 0) { perror("input"); return 1; }

    outadd("Type a command and press START.");
    outadd("");
    outadd("The LimenOS card mounts its Debian root at");
    outadd("/tmp/limen once the Deck app has run; from");
    outadd("there:  chroot /tmp/limen /bin/bash -l");
    draw();

    struct input_event ev;
    int running = 1;
    while (running && read(in, &ev, sizeof ev) == sizeof ev) {
        int dirty = 0;
        if (ev.type == EV_ABS) {
            if (ev.code == ABS_HAT0X && ev.value) { kx = (kx + (ev.value > 0 ? 1 : KCOLS - 1)) % KCOLS; dirty = 1; }
            if (ev.code == ABS_HAT0Y && ev.value) { ky = (ky + (ev.value > 0 ? 1 : KROWS - 1)) % KROWS; dirty = 1; }
        } else if (ev.type == EV_KEY && ev.value == 1) {
            switch (ev.code) {
            case BTN_SOUTH: typech((shift ? UPPER : LOWER)[ky][kx]); dirty = 1; break;
            case BTN_EAST:  if (clen) cmd[--clen] = 0; dirty = 1; break;
            case BTN_NORTH: shift = !shift; dirty = 1; break;
            case BTN_WEST:  typech(' '); dirty = 1; break;
            case BTN_START: if (clen) { run(cmd); clen = 0; cmd[0] = 0; } dirty = 1; break;
            case BTN_TL:    if (scroll > 0) scroll--; dirty = 1; break;
            case BTN_TR:    if (scroll + 7 < nout) scroll++; dirty = 1; break;
            case BTN_SELECT: running = 0; break;
            default: break;
            }
        }
        if (dirty) draw();
    }

    fill(0, 0, W, H, BG);
    munmap(fb, len); close(fd); close(in);
    return 0;
}
