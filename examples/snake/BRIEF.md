# Snake: a first project

Build a very simple Snake game for the web, invent strategies for it, play them thousands of times, and find out which one solves it fastest.

I picked Snake because it's small enough to finish and random enough to need a seed. The game is the setup - the point is the data.

## The game

- Plain web: one HTML page, plain JavaScript, no framework and no build step.
- A 10x10 grid, a snake, one piece of food at a time. Eating grows the snake by one. Hitting a wall or yourself ends the game. Reaching score 20 is a win.
- A 5,000-step cap. A game that hits it ends as `ran_out`.
- You can play it yourself: arrow keys or WASD steer, and any arrow key starts a game.
- A step slider under the board shows the current step. Drag it to scrub back and forth through the game so far, then press Play to carry on from there.
- Fully deterministic from a seed. Food placement, and anything else random, comes from a seeded PRNG. Same seed and same script means the same game, every time.

## Scripting the snake

A script decides the snake's next move. The game ships with none: don't write any strategies into it. The player invents them later and uploads them to the page. There are two kinds:

- **Code:** a `.js` file holding a function, `decide(state) -> move`, where `move` is one of `up`, `down`, `left`, `right`. `state` holds the grid size, the snake's cells, the food and the step count.
- **CSV:** a file of moves, one per line. If the file runs out before the game ends, the game ends there.

The page has a file picker that loads either kind and adds it to the script list. Uploading a file with the same name replaces it. Player strategies live in `strategies/`.

## The runner

A headless runner (Node, or the same JS with rendering off) plays many seeds against every script in `strategies/`. It writes one results CSV with a row per run (one seed played by one script):

```
seed,strategy,grid,steps,score,outcome
```

`outcome` is `won`, `died` or `ran_out` (the CSV ran out, or the game hit the step cap).

## The analysis

Fastest means the fewest steps to score 20: the median `steps` over a strategy's wins. Compare every strategy in `strategies/`. Present the findings as a Claude artifact with charts.

## Done looks like

- The page plays a game you can watch, from a seed and a script you pick, or one you steer with the keyboard, and you can scrub through its steps.
- One seed and one script give the same game, run after run, in the page and in the runner.
- The PRNG and the CSV parser have tests. Run them with a bare `node --test`, since Node 24 reads `node --test test/` as a file.
- You can upload a strategy file to the page and watch it play.
- The runner writes the results CSV for at least 100 seeds per strategy.
- An artifact answers "how often does each strategy win, and how many steps does a win take?", with charts.
