# null: catalogue

Screenshots of null, each with the game's command line that leads back to
it. The page: https://ruescasd.github.io/null-catalogue/

To add shots:

1. In the game, press F12 (or type `shot` at the console). It writes
   `screenshots/STAMP.png` and `STAMP.txt` and keeps the spot as the place
   `shot_STAMP` in `places.txt`.
2. Copy the `.png` and the `.txt` you want into `shots/` here. If you like,
   add a caption line to the `.txt`.
3. Run `python build.py --publish` (it needs Pillow).

See `build.py` for the details.
