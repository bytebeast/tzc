<!-- Set this image as your repo's social preview: Settings > General > Social preview -->
<p align="center">
  <img src="images/tzc-social-preview.png" alt="tzc - paste a timestamp, get your time" width="640">
</p>

<h1 align="center">tzc</h1>

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-a6e3a1?style=flat-square">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.9+-cba6f7?style=flat-square">
  <img alt="Shell" src="https://img.shields.io/badge/shell-bash%20%7C%20zsh-89b4fa?style=flat-square">
  <img alt="fzf" src="https://img.shields.io/badge/picker-fzf-fab387?style=flat-square">
  <img alt="PRs welcome" src="https://img.shields.io/badge/PRs-welcome-a6e3a1?style=flat-square">
</p>

<p align="center"><b>Paste a timestamp, get your local time. Nothing else to think about.</b></p>

---

## Why

Most logs are stamped in **UTC**. When you are staring at an error line, you do
not want to do timezone math in your head. `tzc` is built for exactly that: copy
the timestamp straight out of the log, paste it in, and it tells you what time
that actually was for you, plus how long ago it happened.

It works the other way too. Someone in a different timezone drops a timestamp in
chat ("it broke at 14:35"), and you just paste it in and convert it into your
own timezone without a second thought.

When an incident spans a team spread across three continents, you can pass
`--to` more than once and get every one of those zones in a single block - handy
for a timeline in the postmortem, or for working out whether paging Bengaluru at
that hour was reasonable.

And because your day probably revolves around a handful of the same zones, you
can wrap `tzc` in a couple of **shell aliases** so a conversion is one short
word away.

`tzc` reads basically any timestamp you are likely to copy (SQL, ISO-8601 /
Kubernetes, syslog, Apache, `date` output, Unix epoch in seconds through
nanoseconds, and even plain-English "31 days, 4 hours, 25 minutes ago"), lets
you pick one or more target zones with an `fzf` fuzzy search, and prints the
results in a clean Catppuccin-colored block.

---

## Features

- **Paste and go** - auto-detects roughly a dozen timestamp formats, so you
  rarely have to tell it anything about the input
- **UTC and offset aware** - `Z`, `+02:00`, and named abbreviations (UTC, PST,
  IST, JST, ...) are all understood
- **Unix epoch in any resolution** - seconds, milliseconds, microseconds, or
  nanoseconds, detected automatically
- **Human-readable relative input** - type `31 days, 4 hours, 25 minutes ago` or
  `in 3 hours` and it resolves against now
- **Many zones at once** - repeat `--to` (or give it a comma-separated list) to
  convert one timestamp into every zone your team sits in, in one block
- **fzf timezone picker** - fuzzy-search the full IANA list, annotated with each
  zone's abbreviation and current UTC offset (search `IST` or `-8h`), and press
  `TAB` to select several zones at once
- **Tells you how long ago** - every result includes a friendly relative time
  like `31 days, 4 hours ago`
- **Shell-alias friendly** - pass `--to` to skip the picker and bake your common
  conversions - including whole-team, multi-zone ones - into one-word aliases
- **Readable output** - Catppuccin Mocha colors that auto-disable when piped or
  when `NO_COLOR` is set
- **Single file, standard library only** - the one optional extra is `fzf`, and
  even that has a plain-text fallback

---

## Requirements

- **Python 3.9+** (uses the standard-library `zoneinfo` module)
- **[fzf](https://github.com/junegunn/fzf)** for the interactive timezone
  picker, including `TAB` multi-select. Optional: if `fzf` is not installed, or
  you pass `--to`, `tzc` falls back to a plain text prompt (which accepts a
  comma-separated list of zones) or those values.
- **IANA tz database** - present on macOS and most Linux systems. On a minimal
  install you may need it from PyPI: `pip install tzdata`.

No third-party Python packages are required.

---

## Installation

```bash
# grab the script, name it tzc, make it executable, and put it on your PATH
curl -o tzc https://raw.githubusercontent.com/bytebeast/tzc/main/tzc
chmod +x tzc
mv tzc ~/.local/bin/    # or anywhere on your PATH, e.g. /usr/local/bin

# fzf is recommended for the picker
brew install fzf        # macOS
sudo apt install fzf    # Debian / Ubuntu
```

Then just run `tzc`.

---

## Usage

```
tzc [options] [timestamp]
tzc                       # prompts for a timestamp, then opens the fzf picker
```

### Examples

```bash
# The core use: paste a UTC log line's timestamp, pick your zone in fzf
tzc "2026-07-24T14:35:18Z"

# Skip the picker by naming the target zone
tzc "2026-07-24 14:35:18" --to America/New_York

# Repeat --to for several zones at once - one line of output per zone
tzc "2026-07-24T14:35:18Z" --to America/New_York --to Europe/London --to Asia/Kolkata

# Same thing, comma-separated (mix and match if you like)
tzc "2026-07-24T14:35:18Z" --to America/New_York,Europe/London,Asia/Kolkata

# A teammate pasted their local time in chat; convert it to yours
tzc "Fri Jul 24 07:19:59 PDT 2026" --to Europe/London

# Naive log timestamp with no zone in it - tell tzc it is UTC
tzc "2026-07-24 14:35:18" --from UTC --to Asia/Tokyo

# Unix epoch (seconds, millis, micros, or nanos - auto-detected)
tzc 1721831718 --to Australia/Sydney
tzc 1721831718123456789 --to UTC

# syslog / systemd style (year is assumed to be the current year)
tzc "Jul 24 14:35:18" --to Europe/Paris

# Apache / Nginx access-log timestamp
tzc "24/Jul/2026:14:35:18 +0000" --to America/Chicago

# Plain-English relative time, resolved against now
tzc "31 days, 4 hours, 25 minutes ago" --to UTC
tzc "in 3 hours" --to Asia/Kolkata

# Disable colors (also respects the NO_COLOR convention)
tzc "2026-07-24T14:35:18Z" --to UTC --no-color
```

### One timestamp, every zone your team is in

`--to` is repeatable, and each one also accepts a comma-separated list, so these
are all equivalent:

```bash
tzc 1784903718 --to America/Los_Angeles --to Europe/London --to Asia/Tokyo
tzc 1784903718 --to America/Los_Angeles,Europe/London,Asia/Tokyo
tzc 1784903718 --to America/Los_Angeles,Europe/London --to Asia/Tokyo
```

You get one line per zone, in the order you listed them, with everything else in
the block unchanged:

```
  Timezone Conversion
  ---------------------
Input string : 2026-07-24T14:35:18Z
                -> parsed with explicit timezone
Entered time : 2026-07-24 14:35:18 UTC (+0000)
Converted to : 2026-07-24 07:35:18 PDT (-0700)   [America/Los_Angeles]
               2026-07-24 10:35:18 EDT (-0400)   [America/New_York]
               2026-07-24 15:35:18 BST (+0100)   [Europe/London]
               2026-07-24 20:05:18 IST (+0530)   [Asia/Kolkata]
               2026-07-24 23:35:18 JST (+0900)   [Asia/Tokyo]
UTC          : 2026-07-24 14:35:18 UTC (+0000)
Epoch seconds: 1784903718
Relative     : 46 days, 3 hours, 50 minutes ago
```

Duplicate zones are dropped, so a comma list that overlaps with a flag (or with
an alias you wrapped it in) will not print the same zone twice.

### The fzf picker

Run `tzc` with no `--to` and you get a fuzzy-searchable list of every IANA zone,
each line annotated with its abbreviation(s) and current UTC offset:

```
Asia/Kolkata                    IST         +5:30
America/New_York                EST/EDT     -4h
Europe/London                   GMT/BST     +1h
```

Search by zone name (`tokyo`), by abbreviation (`IST` surfaces India, Ireland,
and Israel so you can pick the right one), or even by offset (`-8h`).

The picker is multi-select: press `TAB` to mark a zone (`Shift-TAB` to unmark),
mark as many as you want, then `Enter` to convert to all of them at once.

---

## Shell aliases

Because you convert to the same few zones all day, wrap them up. Add these to
your `~/.bashrc` or `~/.zshrc`:

```bash
# one-word conversions to your common zones
# --- Americas ---
alias tzsfo='tzc --to America/Los_Angeles'   # SFO  San Francisco
alias tzsea='tzc --to America/Los_Angeles'   # SEA  Seattle
alias tzaus='tzc --to America/Chicago'       # AUS  Austin
alias tzjfk='tzc --to America/New_York'      # JFK  New York
alias tzyyz='tzc --to America/Toronto'       # YYZ  Toronto
 
# --- Europe / Middle East ---
alias tzlhr='tzc --to Europe/London'         # LHR  London
alias tzber='tzc --to Europe/Berlin'         # BER  Berlin
alias tztlv='tzc --to Asia/Jerusalem'        # TLV  Tel Aviv
 
# --- Asia / Pacific ---
alias tzblr='tzc --to Asia/Kolkata'          # BLR  Bengaluru
alias tzszx='tzc --to Asia/Shanghai'         # SZX  Shenzhen
alias tzsin='tzc --to Asia/Singapore'        # SIN  Singapore
alias tzhnd='tzc --to Asia/Tokyo'            # HND  Tokyo
alias tzsyd='tzc --to Australia/Sydney'      # SYD  Sydney

# usage: tzsfo "2026-07-24T14:35:18Z"
```

Since `--to` is repeatable, an alias can cover a whole group of people at once -
your on-call rotation, the team you hand off to, or everyone who will read the
incident timeline:

```bash
# the whole team, in one shot
alias tzteam='tzc --to America/Los_Angeles --to America/New_York --to Europe/London --to Asia/Kolkata'

# follow-the-sun on-call handoff: who is awake right now?
alias tzoncall='tzc --to America/Los_Angeles,Europe/Berlin,Asia/Singapore'

# just the two ends of your handoff window
alias tzhandoff='tzc --to America/New_York,Asia/Kolkata'

# usage: tzteam "2026-07-24T14:35:18Z"
```

Prefer functions so you can convert whatever is on your clipboard in one shot:

```bash
# macOS (pbpaste) - convert the copied timestamp to New York time
tznow() { tzc "$(pbpaste)" --to America/New_York; }

# Linux with xclip - convert the clipboard to your local zone
tzhere() { tzc "$(xclip -o -selection clipboard)"; }

# clipboard -> your zone plus everyone you are working the incident with
tzall() { tzc "$(pbpaste)" --to America/Los_Angeles,Europe/London,Asia/Kolkata; }
```

Now copy a timestamp out of a log, run `tznow` (or `tzall` when you need to
share it), and you are done.

---

## Recognized input formats

| Input example                      | Source                       |
| ---------------------------------- | ---------------------------- |
| `2026-07-24 14:35:18`              | SQL databases, apps (naive)  |
| `2026-07-24T14:35:18Z`             | APIs, Kubernetes (UTC)       |
| `2026-07-24T14:35:18.123Z`         | Cloud-native apps (UTC)      |
| `2026-07-24T14:35:18+02:00`        | ISO-8601 with offset         |
| `Jul 24 14:35:18`                  | Linux syslog (year assumed)  |
| `Jul 24 14:35:18.123`              | systemd, Java (year assumed) |
| `Fri Jul 24 07:19:59 UTC 2026`     | Unix `date` command output   |
| `1721831718`                       | Unix epoch seconds           |
| `1721831718123`                    | Unix epoch milliseconds      |
| `1721831718123456789`              | Unix epoch nanoseconds       |
| `24/Jul/2026:14:35:18 +0000`       | Apache / Nginx access log    |
| `31 days, 4 hours, 25 minutes ago` | Human-readable relative time |
| `in 3 hours, 12 minutes`           | Human-readable relative time |

Naive timestamps (no zone in the string) are assumed to be in your **local**
timezone unless you pass `--from`.

---

## Options

| Flag          | Description                                                                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `--to ZONE`   | Target timezone; skips the fzf picker (e.g. `--to Asia/Tokyo`). Repeatable, and accepts a comma-separated list, to convert to several zones at once |
| `--from ZONE` | Timezone to assume for naive inputs (default: your local zone)                                                                                 |
| `--no-color`  | Disable the Catppuccin colored output                                                                                                          |

Output includes the parsed input, the entered time, the converted time (one line
per `--to` zone), the UTC equivalent, the Unix epoch, and a friendly relative
time.

---

## License

[MIT](LICENSE)
