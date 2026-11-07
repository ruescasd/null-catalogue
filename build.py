"""The catalogue: shots/ made into the page, index.html, with img/ and thumb/.

    python build.py            build
    python build.py --publish  build, then commit and push (GitHub Pages serves it)

A shot is shots/STAMP.txt with shots/STAMP.png beside it, as F12 in the game
writes them to null/screenshots/ (copy both). In the .txt, the line starting
with -- is the way there (the game's command line); any other line is the
shot's caption, optional, added by hand. Shots are shown in file-name order.

The .png stays local (not committed): the page uses img/STAMP.jpg, made from
it. A shot whose .txt is removed is removed from the page.

Each way names a place kept in null/places.txt (`--tp shot_STAMP`): a way
whose place is not there stops the build. The shot places no shot here uses
are listed, to remove from places.txt if wanted.
"""

import argparse
import html
import json
import pathlib
import re
import subprocess
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
SHOTS, IMG, THUMB = ROOT / "shots", ROOT / "img", ROOT / "thumb"
THUMB_WIDTH = 640


def fail(message):
    sys.exit(f"error: {message}")


def read_shot(txt):
    way, caption = None, []
    for line in txt.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("--"):
            if way:
                fail(f"{txt}: two lines start with -- (one is the way there)")
            way = line
        else:
            caption.append(line)
    if not way:
        fail(f"{txt}: no line starting with -- (the way there, as F12 writes it)")
    return {"name": txt.stem, "way": way, "caption": " ".join(caption)}


def make_images(name):
    png, jpg, thumb = SHOTS / f"{name}.png", IMG / f"{name}.jpg", THUMB / f"{name}.jpg"
    if not png.exists():
        if jpg.exists() and thumb.exists():
            return
        fail(f"{png}: missing, and no image made from it before (copy it beside {name}.txt)")
    stamp = png.stat().st_mtime
    if jpg.exists() and thumb.exists() and jpg.stat().st_mtime >= stamp and thumb.stat().st_mtime >= stamp:
        return
    image = Image.open(png).convert("RGB")
    image.save(jpg, quality=90)
    small = image.resize((THUMB_WIDTH, round(image.height * THUMB_WIDTH / image.width)), Image.LANCZOS)
    small.save(thumb, quality=82)
    print(f"made {jpg.name}")


def check_places(shots, places_file):
    if not places_file.exists():
        fail(f"{places_file}: not found (the game's places; --places PATH)")
    kept = set()
    for line in places_file.read_text(encoding="utf-8").splitlines():
        words = line.split()
        if words and not words[0].startswith("#"):
            kept.add(words[0])
    used = set()
    for shot in shots:
        match = re.search(r"--tp (\S+)", shot["way"])
        if not match:
            fail(f"shots/{shot['name']}.txt: its way has no --tp PLACE")
        if match.group(1) not in kept:
            fail(f"shots/{shot['name']}.txt: place {match.group(1)} is not in {places_file}")
        used.add(match.group(1))
    unused = sorted(p for p in kept if p.startswith("shot_") and p not in used)
    if unused:
        print(f"shot places in {places_file} no shot here uses ({len(unused)}): {' '.join(unused)}")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>null</title>
<style>
:root { color-scheme: dark; }
html, body { margin: 0; background: #000; color: #777; font: 12px/1.5 ui-monospace, Consolas, monospace; }
main { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 360px), 1fr)); gap: 4px; padding: 4px; }
main a { display: block; aspect-ratio: 16 / 9; background: #111; }
main img { display: block; width: 100%; height: 100%; object-fit: cover; }
main a:focus-visible { outline: 1px solid #fff; outline-offset: -1px; }
footer { padding: 8px 8px 16px; color: #555; }
#view { position: fixed; inset: 0; background: #000; display: none; }
#view.on { display: block; }
#view img { width: 100%; height: 100%; object-fit: contain; }
#note { position: absolute; left: 12px; right: 12px; bottom: 10px; color: #999; text-shadow: 0 0 4px #000, 0 0 2px #000; pointer-events: none; }
#note .way { color: #777; user-select: all; pointer-events: auto; word-break: break-all; }
#note.off { display: none; }
#prev, #next { position: absolute; top: 0; bottom: 0; width: 25%; cursor: pointer; }
#prev { left: 0; } #next { right: 0; }
</style>
</head>
<body>
<main>__GRID__</main>
<footer>__COUNT__. Under each shot, the game's command line to see it again. In a shot: arrows or the sides to step, i hides the line, Esc closes.</footer>
<div id="view"><img alt=""><div id="prev"></div><div id="next"></div><div id="note"><div class="caption"></div><div class="way"></div></div></div>
<script>
const shots = __DATA__;
const view = document.getElementById("view"), big = view.querySelector("img"), note = document.getElementById("note");
let at = -1;
function show(i) {
  at = (i + shots.length) % shots.length;
  const s = shots[at];
  big.src = "img/" + s.name + ".jpg";
  note.querySelector(".caption").textContent = s.caption;
  note.querySelector(".way").textContent = "game.exe " + s.way;
  history.replaceState(null, "", "#" + s.name);
  for (const j of [at - 1, at + 1]) new Image().src = "img/" + shots[(j + shots.length) % shots.length].name + ".jpg";
}
function open(i) {
  show(i);
  view.classList.add("on");
  if (view.requestFullscreen) view.requestFullscreen().catch(() => {});
}
function close() {
  if (at < 0) return;
  view.classList.remove("on");
  const was = at; at = -1;
  history.replaceState(null, "", location.pathname);
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  document.querySelectorAll("main a")[was].focus();
}
document.querySelectorAll("main a").forEach((a, i) => a.addEventListener("click", e => { e.preventDefault(); open(i); }));
document.getElementById("prev").addEventListener("click", () => show(at - 1));
document.getElementById("next").addEventListener("click", () => show(at + 1));
big.addEventListener("click", close);
document.addEventListener("fullscreenchange", () => { if (!document.fullscreenElement) close(); });
document.addEventListener("keydown", e => {
  if (at < 0) return;
  if (e.key === "Escape") close();
  else if (e.key === "ArrowLeft") show(at - 1);
  else if (e.key === "ArrowRight") show(at + 1);
  else if (e.key === "i") note.classList.toggle("off");
});
const linked = shots.findIndex(s => "#" + s.name === location.hash);
if (linked >= 0) { show(linked); view.classList.add("on"); }
</script>
</body>
</html>
"""


def page(shots):
    grid = "".join(
        f'<a href="img/{s["name"]}.jpg"><img src="thumb/{s["name"]}.jpg" alt="{html.escape(s["caption"])}" loading="lazy"></a>'
        for s in shots
    )
    count = f"{len(shots)} shot{'' if len(shots) == 1 else 's'}"
    data = json.dumps(shots).replace("</", "<\\/")
    return PAGE.replace("__GRID__", grid).replace("__COUNT__", count).replace("__DATA__", data)


def git(*args):
    subprocess.run(["git", "-C", str(ROOT), *args], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--publish", action="store_true", help="also commit and push")
    parser.add_argument("--places", type=pathlib.Path, default=ROOT.parent / "null" / "places.txt", help="the game's places.txt")
    args = parser.parse_args()

    for folder in (SHOTS, IMG, THUMB):
        folder.mkdir(exist_ok=True)
    for png in SHOTS.glob("*.png"):
        if not png.with_suffix(".txt").exists():
            fail(f"{png}: no {png.stem}.txt beside it (F12 writes both; copy them together)")
    shots = [read_shot(txt) for txt in sorted(SHOTS.glob("*.txt"))]
    check_places(shots, args.places)
    for shot in shots:
        make_images(shot["name"])
    names = {s["name"] for s in shots}
    for folder in (IMG, THUMB):
        for jpg in folder.glob("*.jpg"):
            if jpg.stem not in names:
                jpg.unlink()
                print(f"removed {folder.name}/{jpg.name}")
    (ROOT / "index.html").write_text(page(shots), encoding="utf-8")
    print(f"index.html: {len(shots)} shot{'' if len(shots) == 1 else 's'}")

    if args.publish:
        git("add", "-A", "index.html", "img", "thumb", "shots")
        if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode == 0:
            print("nothing changed to publish")
            return
        git("commit", "-m", f"The catalogue: {len(shots)} shots")
        git("push")
        print("pushed; GitHub Pages updates in a minute or so")


if __name__ == "__main__":
    main()
