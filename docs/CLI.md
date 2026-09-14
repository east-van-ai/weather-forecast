# weather-forecast CLI

The grammar is `weather-forecast COMMAND [--flags]`.

```text
weather-forecast run --dry-run [--force]
weather-forecast run --commit [--force]
weather-forecast version
weather-forecast --version
```

`--dry-run` and `--commit` belong to `run`. They are mutually exclusive, and
one of them is required. `--force` belongs to `run` too and combines with
either.

Nothing runs by accident. Bare `weather-forecast` prints the banner, and bare
`run` prints the run command's own documentation. Neither touches anything.
Reaching the pipeline takes a command word and a mode, both typed on purpose.

## Two axes, a command and a mode

The command says what work is asked for. The mode flag says how far to take
it. Keeping the two apart keeps the work out of the flags. A hypothetical
`weather-forecast --run` would be a command word wearing a flag's clothes, and
it would sit in the wrong slot besides.

A flag is the right shape for the mode. `--commit` is the separate, explicit
keystroke that makes a run real. `--dry-run` is the safe end of the same axis:
download, render, describe, log what would be written, and stop.

Neither end is a default. A `run` with no mode flag is an error, exit 1.
Argparse could make the pair required on its own, but its failure exits 2, and
2 is the code for a line argparse could not read. A line missing the mode reads
fine and means nothing, so `main` checks the pair by hand and answers with
weather-forecast's own error.

The safe end could have been the default, as it is in `weed-out`. A bare verb
there already carries the path it acts on, so it has to do something. Here
`run` on its own is free to be a question, so it is one, and the mode stays
spelled out.

## `--force` is a third thing

`--force` bypasses the unchanged-PDF skip. It says nothing about whether the
run writes, so it sits outside the mutually exclusive pair and reads sensibly
with both: `--dry-run --force` re-describes a chart that has not moved, and
`--commit --force` re-posts it.

A dry run consumes the update it previewed. `refresh_pdf` rotates
`current.pdf` to `last.pdf` and downloads either way, so the chart that counted
as new during the preview is the one the next run finds unchanged. Committing
after a preview therefore takes `--force`. A preview that left the files alone
would need a second download path in the downloader, and reusing the flag that
already exists for exactly this costs less.

## A dry run stops before Salesforce

The pipeline never builds the Salesforce client, so the JWT handshake never
happens either. Authenticating would prove the credentials work. The four
`SF_*` variables are still checked before the pipeline starts, and that check
catches the failure that actually happens.

## A lone command word is a question

House style answers a lone command word with that command's documentation,
exit 0, and `run` answers that way. Its docstring carries the mode axis, which
is what a reader needs before typing anything real.

`version` looks like a divergence and is not. It takes nothing and has no mode,
so `version` alone is a complete line. Its answer is documentation whichever
rule you reach for.

## `version` and `--version`

Both spellings print the program name and the installed version on one line,
then exit 0. It is documentation, so it shares its exit code with the banner.

One helper builds that line and both spellings call it. Two independent prints
of the same fact drift apart, and this drift stays invisible until someone
reports the wrong number.

The number is read from the installed distribution metadata, which keeps
`pyproject.toml` the only copy. A tree that has never been built has no
metadata to read, so the lookup is guarded and answers
`unknown (not installed)` instead of raising. The guard matters. The parser is
built on every invocation past a bare word, so an unguarded lookup would take
down `run` as well.

`--version` is defined on the top-level parser only. Asking `run` for the
version is an unknown flag, exit 2.

Neither spelling is advertised. The banner carries the work the tool does, and
a version number is not that. Anyone who wants one goes looking, and this is
where the looking ends.

## Positions are decided, not inferred

Neither command takes a positional, so any bare word after the command is a
stray. `main` reads the slot off the front of the command line with the house
helper, `leading_paths`, instead of trusting what argparse resolved from
elsewhere. The helper keeps its house name so it stays recognizable across the
toolchain, even though nothing it finds here is a path.

## Errors

A command line weather-forecast could not read prints
`weather-forecast: message` to standard error, with the usage line under it.
That covers a stray word and a `run` with no mode flag.

A missing environment variable prints no usage line. The command line was read
fine, so the usage would answer a question nobody asked. The run logs which
variables are missing and stops.

## The grammar is pinned in a test

The accepted grammar sits in a file of its own, `tests/test_cli_grammar.py`. A
command line that drifts from the documented shape still parses, it just means
something else, so nothing fails on its own when the surface moves.

## Exit codes

- **0** covers success, a run skipped because the PDF is unchanged, and
  documentation: the banner, the run docstring, and both version spellings.
- **1** is weather-forecast's own error: a stray word, a `run` with no mode
  flag, a missing environment variable, or a pipeline failure.
- **2** is argparse's own: an unknown command, an unknown flag, or a bad value.

Only 0 and 1 return through `main`. Argparse's 2 and the 0 from `--version`
arrive as a `SystemExit` instead.

## What a run prints

There are no log files. Progress goes to standard error, one line per stage,
and that is the whole record of a run. Since it is standard error and not
standard out, `>` on its own catches nothing. Redirect the stream that carries
it:

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

The slow line is the model. Everything either side of it takes seconds.

## Use of AI

Both the use of AI and its disclosure are deliberate. Code and documentation in
this project are written in collaboration with Artificial Intelligence (AI). The
division of labour: the AI explores, challenges assumptions and edge cases, and
drafts; the human initiates, drafts the designs, explores alongside the AI,
reviews every change, and decides what gets committed.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
