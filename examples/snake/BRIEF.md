# Snake: a first project

Build a very simple Snake game for the web, invent strategies for it, play them thousands of times, and find out which one solves it fastest.

I picked Snake because it's small enough to finish and random enough to need a seed. The game is the setup - the point is the data.

## The game

- Plain web: one HTML page, plain JavaScript, no framework and no build step.
- A 10x10 grid, a snake, one piece of food at a time. Eating grows the snake by one. Hitting a wall or yourself ends the game. Reaching score 20 is a win.
- A 5,000-step cap. A game that hits it ends as `ran_out`.
- You can play it yourself: arrow keys or WASD steer, and any arrow key starts a game.
- A step slider under the board shows the current step. Drag it to scrub back and forth through the game so far. A button labelled `Play` replays from there to the end of the moves, without losing any. Pressing `Play` again at the end carries on live. Steering at a past step plays on from that step and drops the later moves.
- If `context/look.md` exists, the page follows it.
- Fully deterministic from a seed. Food placement, and anything else random, comes from a seeded PRNG. Same seed and same script means the same game, every time. Two scripts on one seed start from the same deal, but a food cell under the snake is skipped, so their games can differ.

## Scripting the snake

A script decides the snake's next move. The game ships with none: don't write any strategies into it. The player invents them later and uploads them to the page.

A script is a plain `.js` file with a top-level function, `decide(state) -> move`, and no `import` or `export`. `move` is one of `up`, `down`, `left`, `right`. `state` holds the grid size, the snake's cells, the food and the step count. A script must not use `Math.random` or the clock, and each game starts it fresh. A move straight back into the neck is ignored.

The page has a button labelled `Strategy file` that loads a `.js` script and adds it to the script list. Picking a strategy waits for `Play`. Uploading a file with the same name replaces it. Player strategies live in `strategies/`.

## The runner

A headless runner (Node, or the same JS with rendering off) plays many seeds against every script in `strategies/`. It writes one results CSV with a row per run (one seed played by one script):

```
seed,strategy,grid,steps,score,outcome
```

`outcome` is `won`, `died` or `ran_out`.

## The analysis

Fastest means the fewest steps to score 20: the median `steps` over a strategy's wins. Compare every strategy in `strategies/`. Present the findings as a Claude artifact with charts.

## After it's built

- **Invent strategies.** The player describes a strategy in plain words, Claude writes it to `strategies/`, and the player uploads it, watches it, scrubs to where it went wrong, and asks for a fix. They go round until they have at least two.
- **Make it look good.** The player may run `/frontend-design:frontend-design` on the finished page. The game rules, slider and upload must keep working, so keep the page's markup and styles easy to change without touching the game code.

## Optional: the moves view

Leave this out of the first build. The player can add it later as its own ticket.

- A moves view beside the board is a small CSV editor holding the game's replay file. It fills in as you play, whoever is playing. The current step's line is highlighted, clicking a line pauses and jumps to that step, and editing a line replays the game from the edited moves. Arrow keys still steer after a click.
- A **replay file** is a CSV of moves, one per line, with `seed,<n>` as its first line, so it plays back the same game. If the moves run out before the game ends, the outcome is `ran_out`. The runner takes one as a script.
- Import and Export buttons load and save the replay file. Import ignores blank lines and spaces, and refuses a file with a bad line, naming it.
- The CSV parser has tests. Playing any game fills the moves view. Exporting it, importing it and pressing Play shows the same game, and editing a move changes the replay.

## Rule details

For anything this brief doesn't settle, pick the simplest rule and write it down. Ask the player only about how it looks and feels.

## Done looks like

- The page plays a game you can watch, from a seed and a script you pick, or one you steer with the keyboard, and you can scrub through its steps.
- One seed and one script give the same game, run after run, in the page and in the runner.
- The PRNG has tests. Run them with a bare `node --test`, since Node 24 reads `node --test test/` as a file. It runs every `.js` under `test/`, so sample scripts go elsewhere. Page behaviour gets a browser check too.
- You can upload a strategy file to the page and watch it play.
- The runner writes the results CSV for at least 100 seeds per strategy.
- An artifact answers "how often does each strategy win, and how many steps does a win take?", with charts.
