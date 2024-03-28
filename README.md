# Lyricsheets

The project in which Google Sheets is both the frontend and the database

## How to use

### Uploading Karaoke Timings

### Populating Songs

To populate a song in Aegisub, add in a `Comment`, set the style to `Song`, then fill in the `Text` field with the title of the song. The line's `Start` should also correspond to the start of the very first timed syllable of the song.

For example, the following line in an .ass file will generate lines for the song `Mitaiken HORIZON`, with the start of the first line timed to `0:03:19.27`:

```ass
Comment: 0,0:03:19.27,0:03:19.27,Song,,0,0,0,,Mitaiken HORIZON
```

Run the `populate_songs.py` script with the following options:

```sh
python populate_songs.py input.ass
```

You can also specify additional .ass files to populate by appending additional files:

```sh
python populate_songs.py input1.ass input2.ass input3.ass ...
```

Running the script on an .ass file with the line earlier will generate three things:

1. A titlecard for the song with `\an7` (top-left aligned) and `200ms` fadein and fadeout. This includes the song title in Romaji and English translation (if it exists), and the names of the composer(s), arranger(s) and writer(s).
2. A list of Romaji lines of the song. Each line is ktimed with a simple `\kf` effect, fades in left to right, fades out left to right, is centered at `(960,960)` or `(960,65)`, and changes color from left to right whenever there is an actor change. For cases where the Romaji and English translation are the same, the line is centered at `(960,1010)`.
3. A list of English translated lines for the song. Each line fades in left to right, fades out left to right, is centered at `(960,1015)` or `(960,120)`, and changes color from left to right whenever there is an actor change. For cases where the Romaji and English translation are the same, an English translated line will be generated, but it will be commented out, so only the Romaji line will be visible for that line.

#### Other flags

`--title <True/False>`

Optional flag. Generates a titlecard for each song if `True`, ignores it if `False`. Defaults to `True`.

`--config <config file path>`

Optional flag. Path to the config file. Defaults to `config.json` in the same directory if not specified.

#### Modifiers

It is possible to make changes to the song line generation without touching the song database. This involves the usage of modifiers, which are included in the `Text` field of the `Song` line.

Here is an example song line, with modifiers:
```
Comment: 0,1:03:18.95,1:03:18.95,Song,,0,0,0,,{\lyricsmodify(Discard,17-;Dupe,1-2,0:01:23.69)}Diamond
```
Modifiers are entered in a similar format to an .ass override tag. Each modifier is delimited with a `;`, and the arguments passed to a modifier are delimited with a `,`. In the above line, there are two modifiers passed to the generation script.

1. Discard, 17-
2. Dupe, 1-2, 0:01:23.69

The first argument will be the modifier name (`Discard` and `Dupe`), which is case-insensitive. The second argument will always be a line range specifier. Valid inputs include the following:

- A single line: `1`, `15`
- A range of lines: `1-3`, `4-15`
- A range of lines until end of song: `3-`, `16-`
- No/All lines specified (also used for modifiers that don't need a range): `-`

The third argument is usually a timedelta specifier. 

- Timedelta: `0:01:00.13`, `-0:01:00.13`

However, some modifiers may take in different or more arguments, which will be specified in the following table.

Here is the list of modifiers:

##### Simple Modifiers

| Modifier | # of Additional Arguments | Description |
| --- | --- | --- |
| Discard | 1 | Discards all specified lines. If line 1 is discarded, the start of the song is now dependent on the first line that is not discarded. |
| Offset | 2 | Offsets all specific lines forward by a specified timedelta. It is possible to offset the lines backward by specifying a negative timedelta.
| Secondary | 1 | Forces the specified lines to become secondary lines (i.e. displayed up top).
| Trim | 2 | Trims the last syllable of the specified lines by a timedelta. This modifies both the length of the line and the karaoke time of the final syllable. It is possible to extend the last syllable by specifying a negative timedelta.
| Dupe | 2 | Duplicates the specified lines, then offsets them forward by a specified timedelta. A duplicated line is processed after all other modifiers are applied to it, and is executed as a deep copy, so further modifications to the original line will not apply to the duplicated line and vice-versa.

##### Complex Modifiers

**Style**

Accepts at least two arguments. The first argument will always be a line range specifier. If there are only two arguments, the second argument will contain an `Actor` value, and the whole line is set to that actor.

If there are more than two arguments, then each argument will be of the following format: `Breakpoint:Actor`. The `Breakpoint` value is the first syllable in the line where `Actor` is applied to, and it remains until the next `Breakpoint`, where there will be a change of `Actor`. Each `Breakpoint` should have a different value.

Example usage:
```
Comment: 0,0:54:17.62,0:55:10.16,Song,,0,0,0,,{\lyricsmodify(Style,-,ren)}Primary
```
*Setting the Actor to `ren` for the song `Primary`.*

**Karaoke**

WIP

**Title**

Accepts two or three arguments. The first argument will always be `-`. The second argument will be the desired song title in Romaji. The third (optional) argument will be the desired song title in English. Regardless of how many arguments is passed to this modifier, all of the titles in the original song will be overridden.

Example usage:
```
Comment: 0,1:42:36.13,1:42:37.26,Song,,0,0,0,,{\lyricsmodify(Title,-,Watashi no Symphony ~Starlines Ver.~,My Symphony ~Starlines Ver.~;)}Watashi no Symphony
```
*Setting the Romaji and English title of `Watashi no Symphony` to `Watashi no Symphony ~Starlines Ver.~` and `My Symphony ~Starlines Ver.~`, respectively.*

**Artist**

Accepts two or more arguments. The first argument will always be `-`. The rest of arguments will be the desired artist(s) for the song, overriding the currently-specified artist within the song database.

Example usage:
```
Comment: 0,0:54:17.62,0:55:10.16,Song,,0,0,0,,{\lyricsmodify(Artist,-,Hazuki Ren)}Primary
```
*Setting the Artist to `Hazuki Ren` for the song `Primary`.*

**Reorder**

WIP

**Retime**

WIP

**Overwrite**

WIP

#### Effects

Effects are a way of generating more powerful kfx for songs using Python scripts. They are loaded by the use of the following modifiers:

**Import**

Accepts two arguments. The first argument will always be `-`. The second argument is the name of the file containing the effects to load. The default behavior is to look in the same directory as the .ass file being populated.

**KFX**

Accepts two arguments. The first argument will always be `-`. The second argument is the name of the effect to use for the particular song, which needs to either be a default effect from within this repository in `lyricsheets/effect/`, or loaded previously via `Import`.

Example usage:
```
Comment: 0,0:38:27.51,0:38:27.51,Song,,0,0,0,,{\lyricsmodify(import,-,chase;kfx,-,chase_effect)}CHASE!
```
*Loads in effects from `chase.py`, then generates KFX for the song `CHASE!` using the effect titled `chase_effect`.*

Other things to note:

1. Multiple effects can be loaded from one file.
2. `Import` only needs to be called once for every file. Once a file and all its effects are loaded, it can be used by any `KFX` modifier in the same .ass file.

Effects can also be loaded for a file via flags when running `populate_songs.py`.

`--effect <name>`

Specifies a default effect to use for all songs within the .ass files passed into the script.

`--force-effect <name>`

Forces an effect to use for all songs within the .ass files passed into the script. Ignores the `KFX` modifier in all songs.

A guide on how to write custom effects is WIP.