# Weather Forecast

## Project structure

```text
data/               Raw data downloads and processed image outputs
salesforce/         Salesforce metadata for deployment
src/
  weather_forecast/
    cli.py          entry point, registered as the `weather-forecast` command
                      via [project.scripts] in pyproject.toml
                      banner, command table, slot reading, dispatch
    args.py         parser, exit codes, USAGE, and the version lookup
    cli_run.py      the run command: its docs, env check, and pipeline call
    chart/          PDF download, PNG conversion, image resizing
    forecast/       vision model inference (WeatherVision)
    orchestration/  pipeline coordinator (WeatherPipeline)
    salesforce/     Salesforce JWT auth and Weather_Report__c upsert
tests/              Test suite for the weather forecast application
```

## Command line

The grammar is `weather-forecast COMMAND [--flags]`.

```text
weather-forecast run --dry-run [--force]
weather-forecast run --commit [--force]
weather-forecast version
weather-forecast --version
```

`--dry-run` and `--commit` belong to `run`, are mutually exclusive, and one of
them is required. `--force` belongs to `run` too and combines with either.

Nothing runs by accident. Bare `weather-forecast` prints the banner, bare `run`
prints the run command's own documentation, and neither touches anything.
Reaching the pipeline takes a command word and a mode, both typed on purpose.

### Two axes, a command and a mode

The command says what work is asked for. The mode flag says how far to go with
it. Holding the two apart is what keeps the work out of the flags: a
hypothetical `weather-forecast --run` would be a command word wearing the wrong
clothes, and it would sit in the wrong slot besides.

How far to go is the other axis, and a flag is the right shape for it.
`--commit` is the separate, explicit keystroke that makes a run real.
`--dry-run` is the safe end of the same axis: download, render, describe, log
what would be written, and stop.

Neither end is a default. A `run` carrying no mode flag is an error, exit 1.
Argparse can make the pair required on its own, but its failure exits 2, and 2
is the code for a line argparse could not read. A line missing the mode reads
fine and means nothing, so `main` checks the pair by hand and answers with
weather-forecast's own error.

The safe end could have been the default, which is what `weed-out` does, but a
bare verb there already carries the path it acts on, so it has to mean
something. Here `run` on its own is free to be a question, so it is one, and
the axis stays spelled out.

### `--force` is a third thing

`--force` bypasses the unchanged-PDF skip. It says nothing about whether the
run writes, which is why it sits outside the mutually exclusive pair and reads
sensibly against both: `--dry-run --force` re-describes a chart that has not
moved, `--commit --force` re-posts it.

A dry run consumes the update it previewed. `refresh_pdf` rotates
`current.pdf` to `last.pdf` and downloads either way, so the chart that counted
as new during the preview is the one the next run finds unchanged. Committing
after a preview therefore takes `--force`. A non-mutating preview would mean a
second download path in the downloader, which costs more than reusing the flag
that already exists for exactly this.

### A dry run skips the Salesforce stage whole

The JWT handshake never happens either. Authenticating would prove the
credentials work, but the four `SF_*` variables are checked before the pipeline
starts, which catches the failure that actually happens.

### A lone command word is a question

House style answers a lone command word with that command's documentation,
exit 0, and `run` answers that way. Its docstring carries the mode axis, which
is what a reader needs before typing anything real.

`version` looks like a divergence and is not. It takes nothing and it has no
mode, so `version` alone is a complete line, and its answer is documentation
whichever rule you reach for.

### `version` and `--version`

Both spellings print the program name and the installed version on one line,
then exit 0. It is documentation, so it shares its exit code with the banner.

One helper builds that line and both spellings call it. Two independent prints
of the same fact drift apart, and this is a fact where drift stays invisible
until someone reports the wrong number.

The number is read from the installed distribution metadata, which keeps
`pyproject.toml` the only copy. A tree that has never been built has no
metadata to read, so the lookup is guarded and answers
`unknown (not installed)` instead of raising. The guard matters because the
parser is built on every invocation past a bare word, so an unguarded lookup
would take down `run` as well.

`--version` is defined on the top-level parser only. Asking `run` for the
version is an unknown flag, exit 2.

Neither spelling is advertised. The banner carries the work the tool does, and
a version number is not that. Anyone who wants one goes looking, and this is
where the looking ends.

### Positions are decided, not inferred

Neither command takes a positional, so any bare word after the command is a
stray. `main` reads the slot off the front of the command line with the house
helper instead of trusting what argparse resolved from elsewhere. The helper
keeps its house name, `leading_paths`, so it stays recognizable across the
toolchain, even though nothing it finds here is a path. A stray gets
weather-forecast's own error with the usage line under it, exit 1.

### Layout

`args.py` sits beside `cli.py` and holds the parser, the exit codes, the
version lookup, and the one `USAGE` line. The whole grammar fits on that
line, so both commands share it instead of carrying one each.

`cli_run.py` holds the run command's own documentation, the environment check,
and the call into the pipeline. Logging is configured there rather than in
`main`, which is what lets `version` answer with one line and no log preamble
above it.

`version` gets no module. It is one print, and it stays in `cli.py` beside the
command table.

`cli.py` keeps the banner, the command table, the slot reading, the usage
error, and `main`.

The accepted grammar is pinned in a test file of its own. A command line that
drifts from the documented shape still parses, it just means something else,
so nothing fails on its own when the surface moves.

### Exit codes

0 covers success, a run skipped because the PDF is unchanged, and
documentation, which is the banner, the run docstring, and both version
spellings. 1 is weather-forecast's own error: a stray token, a `run` with no
mode flag, a missing environment variable, or a pipeline failure. 2 is
argparse's own: an unknown command, an unknown flag, or a bad value. Only 0
and 1 return through `main`.

## The chart

One URL, the JMA quick-look surface analysis:

<https://www.data.jma.go.jp/yoho/data/wxchart/quick/ASAS_COLOR.pdf>

The PDF holds nothing but the chart image, so page one rendered to PNG is the
whole document. The model reads the PNG, never the PDF.

Where the files land depends on how the command was installed. A pipx install
writes to `~/.cache/weather-forecast/data/`, since a pipx user has no checkout
to write into. Every other install writes to `./data` beside the working
directory.

Two PDFs are kept, `current.pdf` and `last.pdf`. Comparing their hashes is the
only thing that decides whether a run has new work to do.

## Vision model

The model is `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`.

State the bar first, because it decides everything below it. The prompt asks
"What is this?". The run is a success if the answer describes a weather chart.
Nothing in this project forecasts anything, despite the name. The chart is a
JMA surface analysis, and the model is reading it, not interpreting it.

Memory picks the model. The machine is an M1 MacBook Air with 8 GB. Weights on
disk, measured rather than guessed from the parameter count:

| model | bytes | stored as |
| --- | --- | --- |
| SmolVLM2-500M-Video-Instruct | 2.03 GB | fp32 |
| SmolVLM2-2.2B-Instruct | 8.99 GB | fp32 |

The 2.2B is the interesting one and it stays on the shelf. It does not fit at
full width, and every route to a quantized copy leaves torch behind: the MLX
build needs `mlx-vlm`, the GGUF build needs llama.cpp, and bitsandbytes has no
working MPS backend. That is a runtime decision, not a model decision, and it
deserves its own round.

The odd name is upstream. SmolVLM2 ships its small sizes only as
`-Video-Instruct`. Still images are fine.

The licence is Apache 2.0.

### Why the prompt stays short

"What is this?" is the whole prompt, and asking for more makes the answer
worse. Prompts that requested analysis produced a temperature of 20°C, a
pressure of 1000 mb, and a storm near Guam. None of that is on a surface
analysis in any form this model could read. Two prompts run against the same
image then disagreed on whether the weather was clear or overcast, which is
what settles it. The figures come from the question, not from the page.

So the prompt asks the one thing the model can answer from pixels, and the
answer names the JMA. The longer prompts were also three to five times slower,
and they tended to hit the token cap partway through repeating themselves.

### The full render, never the thumbnail

The processor splits the image into sub-crops and emits a fixed token budget
either way, so a smaller source image buys nothing and costs signal. Fed the
300px thumbnail, the model called a JMA surface analysis a map of the United
States. Fed the full render, it named the JMA. Splitting stays on for the same
reason: turned off, the whole chart collapses to 79 tokens and the answer
wanders off to the Pacific Ocean and repeats itself until the token cap.

The full render is a requirement, not a convenience, and it is written on
`_generate_forecast`.

### `num2words` and `torchvision` are real dependencies

SmolVLM2's processor imports `num2words` and raises on `from_pretrained`
without it. Nothing in the project imports it by name, so it is pinned in
`pyproject.toml` alongside `docopt`, which it pulls in turn.

`torchvision` is the same trap one level up. `processing_smolvlm.py` imports
the video processor at module scope, and that module imports
`torchvision.transforms.v2`. No video is ever processed here and the import
happens anyway, so a build without `torchvision` cannot construct the
processor at all. What it raises is `ModuleNotFoundError: Could not import
module 'SmolVLMProcessor'`, which names the processor and not the missing
package, so the error sends the reader to the wrong place.

All three are as load-bearing as `cryptography`, and as easy to prune by
mistake.

### The prompt is built by the processor

SmolVLM2 splits the image into sub-crops first, and `apply_chat_template` then
emits however many image tokens that produced. A hand-written `<image>`
placeholder cannot know that count, so the template builds the prompt and no
literal placeholder appears in the text.

Decoding follows from the same fact. A chat template puts the user turn
inside the output sequence, so decoding the whole thing hands back the prompt
along with the answer. Only the generated tail is decoded.

## Salesforce

The generated text is uploaded with `simple_salesforce`, a thin REST API
client, and lands on a `Weather_Report__c` record. Nothing heavier sits in the
way: no MuleSoft, no data loader, no middleware. One record per run does not
need a platform behind it.

### OAuth connection

Authentication is Salesforce's OAuth 2.0 JWT Bearer flow. No browser, no
redirect, and no interactive step, which is what lets an unattended run work.
The assertion is signed with RS256, posted to the org's token endpoint, and
the returned session is handed to `simple_salesforce`.

The org side is set up before the first run: a connected app, a certificate,
and the four `SF_*` environment variables carrying the username, client id,
audience, and private key. Those variables are read from the environment and
from nowhere else, so weather-forecast never keeps a credential of its own.

## The log

There are no log files. Progress goes to standard error, one line per stage,
and that is the whole record of a run. It is standard error and not standard
out, so `>` on its own catches nothing. Redirect the stream that carries it:

```bash
weather-forecast run --commit --force 2> run.log
```

A full run reads like this:

```text
2026-08-31 10:02:18,143 INFO weather_forecast.cli_run - Execution started (mode=commit, force=True)
2026-08-31 10:02:18,143 INFO weather_forecast.orchestration.pipeline - Pipeline run started
2026-08-31 10:02:18,362 INFO weather_forecast.orchestration.pipeline - Preparing images
2026-08-31 10:02:20,146 INFO weather_forecast.orchestration.pipeline - Generating forecast via AI
2026-08-31 10:03:13,968 INFO weather_forecast.orchestration.pipeline - Publishing results to Salesforce
2026-08-31 10:03:16,821 INFO weather_forecast.orchestration.pipeline - Salesforce publish completed: record_id=a00gK00001EFOh8QaH created=False
2026-08-31 10:03:16,821 INFO weather_forecast.orchestration.pipeline - Pipeline run completed successfully
2026-08-31 10:03:16,829 INFO weather_forecast.cli_run - Pipeline executed successfully
```

The slow line is the model. Everything either side of it is seconds.

## Dependencies

Dependencies are declared once, in `pyproject.toml`. There are no
requirements files. A requirements file restates what `[project.dependencies]`
already carries, and a freeze kept beside the table drifts out of step with it
within days.

`[project.dependencies]` keeps the full pinned set, transitive entries
included. That is a lockfile living in the dependency table, and it is
deliberate: a proof of concept pinned to one tested combination is worth more
than one that resolves freshly and stops working.

`[dependency-groups]` holds a `dev` group, in the shape every project in the
toolchain uses: `black` and `ruff` pinned, `pytest`, `pytest-cov`, and
`pytest-mock` left to float. The split is on purpose. A formatter that moves
underneath you reformats the tree on its own, so it is pinned. A test runner
does not, so it is not.

The group is not a second freeze. `iniconfig`, `pluggy`, and `Pygments` reach
an install only through pytest, so neither the table nor the group names them
and pip resolves them. Keeping the test tooling out of the runtime table is
what lets a `pipx` install of the command carry no test runner.

Installing:

```bash
pip install -e .                # runtime only
pip install -e . --group dev    # runtime plus the tests
```

`--group` arrived in pip 25.1, so an older pip cannot read the group.

`cryptography` looks unused and is not. It reaches the project through
PyJWT's `crypto` extra, which RS256 signing needs, and the JWT handshake signs
with RS256. Nothing imports it by name, so it survives only if whoever prunes
this table knows why it is there.

## Use of AI

Both the use of AI and its disclosure are deliberate. Code and
documentation in this project are written in collaboration with
Artificial Intelligence (AI). The division of labour: the AI explores,
challenges assumptions and edge cases, and drafts; the human
initiates, drafts the designs, explores alongside the AI, reviews
every change, and decides what gets committed.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
