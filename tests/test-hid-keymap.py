#!/usr/bin/env python3
"""
LimenOS — verify limen-hid emits correct USB HID boot-keyboard reports.

Independent check: this decoder is built from the HID Usage Table
(Keyboard/Keypad page 0x07) directly, NOT from limen-hid's own table, so a
wrong keycode in the shell script cannot pass by agreeing with itself.

  python3 tests/test-hid-keymap.py
"""
import os, subprocess, sys, tempfile, pathlib

HID = pathlib.Path(__file__).resolve().parent.parent / "device" / "limen-hid"

# HID Usage Table 0x07 -> (unshifted, shifted)
USAGE = {
    0x04:("a","A"),0x05:("b","B"),0x06:("c","C"),0x07:("d","D"),0x08:("e","E"),
    0x09:("f","F"),0x0a:("g","G"),0x0b:("h","H"),0x0c:("i","I"),0x0d:("j","J"),
    0x0e:("k","K"),0x0f:("l","L"),0x10:("m","M"),0x11:("n","N"),0x12:("o","O"),
    0x13:("p","P"),0x14:("q","Q"),0x15:("r","R"),0x16:("s","S"),0x17:("t","T"),
    0x18:("u","U"),0x19:("v","V"),0x1a:("w","W"),0x1b:("x","X"),0x1c:("y","Y"),
    0x1d:("z","Z"),
    0x1e:("1","!"),0x1f:("2","@"),0x20:("3","#"),0x21:("4","$"),0x22:("5","%"),
    0x23:("6","^"),0x24:("7","&"),0x25:("8","*"),0x26:("9","("),0x27:("0",")"),
    0x2c:(" "," "),
    0x2d:("-","_"),0x2e:("=","+"),0x2f:("[","{"),0x30:("]","}"),0x31:("\\","|"),
    0x33:(";",":"),0x34:("'",'"'),0x35:("`","~"),
    0x36:(",","<"),0x37:(".",">"),0x38:("/","?"),
}
NAMED = {0x28:"<ENTER>",0x29:"<ESC>",0x2a:"<BKSP>",0x2b:"<TAB>",0x4c:"<DEL>",
         0x3a:"<F1>",0x45:"<F12>",0x52:"<UP>",0x51:"<DOWN>",0x50:"<LEFT>",0x4f:"<RIGHT>"}
MODNAME = {1:"CTRL",2:"SHIFT",4:"ALT",8:"GUI"}

def run(args, env_extra=None):
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".bin"); out.close()
    env = dict(os.environ, LIMEN_HID_DEV=out.name, LIMEN_HID_DELAY="0")
    if env_extra: env.update(env_extra)
    r = subprocess.run(["sh", str(HID)] + args, env=env,
                       capture_output=True, text=True)
    data = open(out.name,"rb").read(); os.unlink(out.name)
    return data, r

def reports(data):
    assert len(data) % 8 == 0, f"report stream not a multiple of 8 bytes: {len(data)}"
    return [data[i:i+8] for i in range(0,len(data),8)]

def decode_text(data):
    """Decode press/release pairs back into a string."""
    s=[]
    for rep in reports(data):
        mod, resv, k = rep[0], rep[1], rep[2]
        assert resv == 0, f"byte 1 (reserved) must be 0, got {resv}"
        assert rep[3:] == b"\x00"*5, "keys 2-6 should be empty for single taps"
        if k == 0:
            continue                      # release
        if k in USAGE:
            s.append(USAGE[k][1 if mod & 2 else 0])
        elif k in NAMED:
            s.append(NAMED[k])
        else:
            s.append(f"<0x{k:02x}>")
    return "".join(s)

def decode_combo(data):
    rep = reports(data)[0]
    mods = [n for b,n in MODNAME.items() if rep[0] & b]
    k = rep[2]
    key = USAGE.get(k,(None,None))[0] or NAMED.get(k) or f"0x{k:02x}"
    return sorted(mods), key

FAIL=0
def check(label, got, want):
    global FAIL
    if got == want:
        print(f"  \033[32m✓\033[0m {label}")
    else:
        FAIL += 1
        print(f"  \033[31m✗\033[0m {label}\n      got  {got!r}\n      want {want!r}")

print("\n=== limen-hid report verification ===\n")
print("-- literal strings round-trip --")
for s in ["hello", "Hello World", "abcXYZ", "1234567890",
          "sudo rm -rf /tmp/x", "a_b-c=d+e", "p@ssw0rd!", 'say "hi"',
          "a/b\\c|d", "{[()]}", "~`<>,.?/;:'"]:
    data, r = run(["type", s])
    check(f"type {s!r}", decode_text(data), s)

print("\n-- every printable ASCII char --")
import string
printable = string.ascii_letters + string.digits + " !@#$%^&*()-_=+[]{}\\|;:'\",.<>/?`~"
missing=[]
for ch in printable:
    data, r = run(["type", ch])
    if not data:
        missing.append(ch); continue
    if decode_text(data) != ch:
        missing.append(ch)
if missing:
    FAIL += 1
    print(f"  \033[31m✗\033[0m {len(missing)} char(s) wrong/unmapped: {''.join(missing)!r}")
else:
    print(f"  \033[32m✓\033[0m all {len(printable)} printable ASCII chars map correctly")

print("\n-- key combinations --")
for args, want in [ (["GUI","r"], (["GUI"],"r")),
                    (["CTRL","ALT","DELETE"], (["ALT","CTRL"],"<DEL>")),
                    (["ENTER"], ([], "<ENTER>")),
                    (["CTRL","SHIFT","ESC"], (["CTRL","SHIFT"],"<ESC>")),
                    (["ALT","F4"], (["ALT"],"<F1>")) ]:
    data, r = run(["key"]+args)
    got = decode_combo(data)
    if args == ["ALT","F4"]:
        rep = reports(data)[0]
        check("key ALT F4 -> mod=ALT keycode=0x3d", (rep[0], rep[2]), (4, 0x3d))
    else:
        check(f"key {' '.join(args)}", got, want)

print("\n-- release frames --")
data,_ = run(["type","ab"])
r = reports(data)
check("press/release pairs", len(r), 4)
check("every 2nd report is a release", all(x == b"\x00"*8 for x in r[1::2]), True)

print("\n-- safety: run refuses without --arm --")
tmp = tempfile.NamedTemporaryFile("w", suffix=".ducky", delete=False)
tmp.write("REM test\nSTRING hello\nENTER\n"); tmp.close()
data, r = run(["run", tmp.name])
check("exits non-zero without --arm", r.returncode != 0, True)
check("emits no keystrokes without --arm", len(data), 0)
check("explains why", "--arm" in (r.stderr+r.stdout), True)

print("\n-- ducky script with --arm --")
data, r = run(["run", tmp.name, "--arm"])
check("ducky STRING+ENTER", decode_text(data), "hello<ENTER>")
os.unlink(tmp.name)

print("\n-- ducky: comments and CRLF ignored --")
tmp = tempfile.NamedTemporaryFile("w", suffix=".ducky", delete=False)
tmp.write("REM a comment\r\n# another\r\nSTRING hi\r\n"); tmp.close()
data, r = run(["run", tmp.name, "--arm"])
check("CRLF + comments", decode_text(data), "hi")
os.unlink(tmp.name)

print()
if FAIL:
    print(f"\033[31m{FAIL} check(s) FAILED\033[0m\n"); sys.exit(1)
print("\033[32mall checks passed\033[0m\n")
