# NeoSharp

A NeocronSharp lite client: only **Research** and **Construction** from [NeocronSharp](https://github.com/sheepnotlost/NeocronSharp), with no tracker, walking, combat or memory reading. It reads the game from screenshots and local Windows OCR, and sends ordinary mouse and keyboard input.

Double-click **Launch.cmd**. Everything it needs, Python included, is in `runtime/`, so there is nothing to install. **Check-Dependencies.cmd** checks the bundle without touching the game.

**No coordinate calibration:** Processor, Start, Inventory and the quantity dialog are found on screen at any resolution, fullscreen or windowed, and at any UI scale (about .6x to 2.2x). Keep their controls visible. Screenshots are never uploaded.

## Controls

**Start in 3 seconds** is the only action button, with no hotkeys. Start it, then click into Neocron before the countdown ends. Switching away stops the batch, with no automatic resume. Closing NeoSharp also stops it and releases anything it was holding.

If a run stops, the last game frame is saved to `diagnostics/latest.png` and the reason to `diagnostics/latest.json`. Settings live in `profile.json` and status in `macro.log`.

## Research

**Tech parts (T / E / A / L):**

1. In Neocron, open Inventory and Processor. Put the research tool in the first Processor slot, leave the other inputs empty, and keep one visible stack of each type you want.
2. Enter each stack's real **Available** size and how many to **Research**. Zero skips a type.
3. Click **Start in 3 seconds** and focus Neocron.

Each cycle drags one part to the Processor, checks the quantity dialog shows exactly 1, presses Start and waits for the input to clear. There are no research timers. The last result stays in the Processor. After a stop, check the item and your counts before starting again.

**Item → blueprint:** set **Copies per batch**, or **0** to repeat until you switch away. Prepare the research tool, the item and empty datacubes yourself. The macro only presses Start, watches the progress and confirms each blueprint before starting the next.

## Construction

**Catalog** lists 1,263 item entries you can search by name or shorthand, taken from the [Tech Haven Items DB](https://db.techhaven.org/en/) on 26 October 2026. Most are marked **Check blueprint**: the site doesn't prove a blueprint exists. **Use blueprint recipe** saves an item to the Job page.

1. On **Job**, choose a saved recipe or type a blueprint's name. **WP7**, **WP9** and **HH** pick the built-ins. Aliases are optional.
2. In Neocron, open Inventory and Processor, put the construction tool in the first Processor slot, and keep the blueprints and ingredients in Inventory. Scroll Inventory to the top: the search runs downward.
3. Enter **Build this batch**, or **0** to build until the blueprints run out.
4. Click **Start in 3 seconds** and focus Neocron.

It drags one blueprint in, confirms quantity 1, presses Start and watches for the result. **Ingredients are never dragged or clicked: Neocron supplies them.** Any unclear state, missing item or focus loss stops the batch, and an uncertain transfer is never retried.

**Search:** **Fast** checks only what looks like a datacube. If an unusual icon is missed, use **Thorough**, which checks every cell.

**Queue:** fill the form and click **Add job** for each item, then Start builds them in order, each row counting down. A job that runs out of blueprints or materials is skipped and reported, and stays queued for a retry. Scrolling Inventory back up and taking back a refused blueprint haven't been tested live yet.

**More Materials in GoGo:** with a GoGuardian window open beside Inventory and Processor, a build refused for missing materials takes up to 15 of each needed ingredient from GoGuardian, then tries again. Not tested live yet.

**Count slots** tracks 0 to 5 slots across the batch. **Stop at N or more slots** ends the batch on the first result that qualifies and leaves it in the Processor.

## Skins and sound

The **Skin** selector has 15 skins, none of which affect game detection. **Sound when stopped** is optional and plays one tone when a batch ends.

## For developers

```powershell
.\runtime\python.exe -m unittest discover -s tests
.\runtime\python.exe app.py --check
.\runtime\python.exe app.py --smoke-ui
```

`--check` validates saved settings and `--smoke-ui` opens and closes the panel; neither sends game input.

Python license: `runtime/LICENSE.txt`. Library licenses are in `runtime/Lib/site-packages`, and Tcl/Tk's are in `runtime/tcl`.
