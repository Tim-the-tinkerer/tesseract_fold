# tesseract_fold.py

`tesseract_fold.py` scrambles and restores text or bytes by folding a tesseract.

A tesseract is a four-dimensional cube: 16 vertices, 32 edges, 24 square faces, and 8 cubic cells. The program sets each symbol on a vertex of a hypercube, folds that hypercube, and reads the vertices back in coordinate order. The symbols stay the symbols. Only their positions change.

Python 3.10 or newer is enough. There is nothing to install.

This is obfuscation. Anyone who can run the program and knows the key can reverse it. Folding the folded text again is a different rearrangement. Unfold with `--decrypt`. For real encryption, use `AES_file`.

## Easy launch — numbered menu

There is no installation and no server.

- **macOS:** double-click **`Tesseract Fold.command`**. If macOS blocks it, Control-click the file and choose **Open**. If it opens as text, run `bash "Tesseract Fold.command"` in Terminal.
- **Windows:** double-click **`Tesseract Fold.bat`**. It tries the `py -3` launcher first, then `python`.
- **Linux / Terminal:** run `python3 tesseract_fold.py` in this folder. `python3 tesseract_fold.py --menu` opens the same menu.

```text
TESSERACT FOLD — geometric folds of a 4D hypercube

  1. Fold text
  2. Unfold text
  3. Fold a file
  4. Unfold a file
  5. Show a fold map
  6. Fold analysis
  7. Repeated-fold experiment
  8. Custom fold sequence
  9. Permutation explorer
 10. Fold a folder
 11. Unfold a folder
  0. Exit
```

Text in the menu is one line. A file keeps every byte. A file path can be typed or dragged in from Finder; a dragged name may show backslashes before spaces and commas, and those are read as the name on disk. Press Enter at the key prompt to leave the key empty. Folding then asks `Passes [1], or legacy:`. Enter uses one multiscale pass. A number from 1 to 16 uses that many passes, each with its own folds. The word `legacy` uses the older geometry, and an empty key there is the six canonical folds. Unfolding a file follows the header and does not ask. Enter `:back` to cancel the step. A new file written from the menu includes a short header. If the destination is already there, the menu asks before replacing it.

Choice 6 prints the analysis and then the folded line. Choice 7 asks for text or a length such as `16`, then reports how many repetitions restore the original arrangement. Choice 8 prints the fold names, takes a sequence such as `xy+,xy+,xy+,mw,hx+`, and asks whether to fold or unfold. Enter folds. `u` unfolds with that same sequence. That choice stays on the older geometry and does not ask for passes. Choice 9 takes a length, a key, and an optional second key, and compares one multiscale pass. Enter skips the comparison. Choice 10 packs a folder into one `.tess` package. Choice 11 restores that package into a new folder. Neither asks for a compression method.

## Run it from the command line

From this folder:

```bash
python3 tesseract_fold.py Hello
python3 tesseract_fold.py --passes 2 --key paper Hello
python3 tesseract_fold.py --legacy Hello
python3 tesseract_fold.py --legacy --decrypt lloeH
python3 tesseract_fold.py --legacy --key paper Hello
python3 tesseract_fold.py --map Hello
python3 tesseract_fold.py --analyze Hello
python3 tesseract_fold.py --repeat Hello
python3 tesseract_fold.py --folds xy+,zw+,xz+,yw+,mw,dxw Hello
python3 tesseract_fold.py --explore --length 16 --compare=
python3 tesseract_fold.py --check
python3 tesseract_fold.py --folder MyFolder
python3 tesseract_fold.py --decrypt MyFolder.tess --output MyFolder-restored
```

| Argument | Meaning |
| --- | --- |
| `TEXT` | Words to fold or unfold, joined by single spaces. A trailing newline is printed after them and is not part of the result. |
| `FILE` | An existing file. A single directory is packed as a folder. Every name on the line has to be a file, or the words are one message. |
| `--decrypt`, `-d` | Put the symbols back. A keyed file needs the same key. A version 3 file carries its fold sequence. A version 4 file carries its pass count. |
| `--key`, `-k` `PHRASE` | Choose the folds from the phrase. `--key=paper` is the same as `--key paper`. The phrase is not stored. Cannot be combined with `--folds`. |
| `--legacy` | Use the older geometry. With no key that is the six canonical folds, and `Hello` folds to `lloeH`. A key is 4 to 7 catalog folds. A headerless result from that geometry, including an older pipe, needs `--legacy` again to unfold. |
| `--passes` `N` | Multiscale passes, from 1 to 16. Each pass derives its own folds from the key and the pass number. The default is 1. A file records the count. Cannot be combined with `--legacy` or `--folds`. |
| `--folds` `SPEC` | Use these folds, in this order, instead of a key. This is always the older geometry. A file records the list. `--raw` does not, so unfolding then needs the same `--folds`. |
| `--file`, `-f` `PATH` | Read this file. `--file=-` reads standard input. A directory is packed as a folder. |
| `--folder` `PATH` | Pack this folder, or, with `--decrypt`, restore this package. The tree is stored, not compressed, and folded as one message. |
| `--output`, `-o` `PATH` | Write the result here. Parent folders are created. One file at a time. |
| `--binary` | Fold raw bytes. Typed text is still read as UTF-8 and then folded as those bytes. |
| `--force` | Replace an existing `--output` file without asking. Required when the command is not running at a terminal. |
| `--header` | Prepend a one-line header on fold. Files do this unless `--raw` is set. |
| `--raw` | On fold, do not write a header. On unfold, do not look for one. |
| `--map`, `-m` | Trace the folds on standard error. The folded output is unchanged. |
| `--trace` `INDEXES` | Follow these write indexes in the map, for example `--trace 0,4`. Implies `--map`. |
| `--analyze`, `--analysis` | Print a fold analysis on standard error and still write the folded result. |
| `--repeat` | Print how many repetitions of the whole sequence restore the arrangement. No folded file is written. |
| `--explore` | Describe the permutation of a length. No document and no folded file. |
| `--length` `N` | The length for `--explore` or `--repeat` when there is no message. The default explore length is 16. |
| `--compare` `PHRASE` | With `--explore`, ask whether this key is the same permutation. `--compare=` uses the canonical folds. |
| `--compare-folds` `SPEC` | With `--explore`, compare with this fold list instead of a key. |
| `--text`, `-t` | Fold the words themselves, even when a file of that name exists. |
| `--menu` | Open the numbered menu. It cannot be combined with other arguments. |
| `--check` | Check the folds and the Hello example, then exit. |
| `--` | Words after this are text, including words that start with `-`. |

Flags can sit before or after the words.

With no arguments, a terminal opens the numbered menu. A pipe is one message. Every byte is kept, and no extra newline is added.

`Hello` with no extra flags takes one multiscale pass. The symbols are still the letters of `Hello`, in a different order.

`Hello` with `--legacy` prints:

```text
lloeH
```

`Hello` with `--legacy --key paper` prints:

```text
oHell
```

## What a fold does

The smallest grid is one tesseract. Each axis is 0 or 1, so there are 16 vertices `(x, y, z, w)`. A longer message uses the next hypercube whose side is a power of two: 16 vertices, then 256, then 4096, and so on. Side 4 is a 2×2×2×2 packing of tesseracts. The side comes from the length alone. Empty vertices are not written out, so the result has the same length as the input.

Write order numbers the vertices with x fastest:

```text
x = i mod S
y = (i // S) mod S
z = (i // S²) mod S
w = (i // S³) mod S
```

`Hello` lands on the first five vertices:

```text
w=0
  z=0
    y=0  H e
    y=1  l l
  z=1
    y=0  o .
```

x increases to the right. y increases downward. `.` is an empty vertex.

Four kinds of fold are used. Each one is an isometry of the grid, so it never stacks two symbols on one vertex.

- A **quarter-turn** in the plane of axes a and b sends `(p, q)` to `(S-1-q, p)`. That is one counterclockwise swing about those two axes, the hinge that folds a cube of a tesseract net around a square face. Four turns restore the vertex. Three turns are one clockwise turn. Short names are `xy+` and `xy-`, and the same for `xz`, `xw`, `yz`, `yw`, and `zw`.
- A **mirror** reflects one axis through the middle: `p` becomes `S-1-p`. The names are `mx`, `my`, `mz`, and `mw`.
- A **diagonal crease** swaps two axes. The names are `dxy`, `dxz`, `dxw`, `dyz`, `dyw`, and `dzw`.
- A **slab fold** reflects inside the lower or upper half of one axis and leaves the other half where it is. On a single tesseract each half is one point thick, so a slab fold does nothing there. It starts to move vertices at side 4. The names are `hx-` and `hx+` for the lower and upper halves of x, and the same for y, z, and w.

`#0` through `#31` pick a catalog entry. Names are not case-sensitive. Commas or spaces separate them. The canonical six are `xy+,zw+,xz+,yw+,mw,dxw`.

With `--legacy` and no key, every message takes those six folds:

1. Quarter-turn counterclockwise in the xy plane.
2. Quarter-turn counterclockwise in the zw plane.
3. Quarter-turn counterclockwise in the xz plane.
4. Quarter-turn counterclockwise in the yw plane.
5. Mirror through the middle, perpendicular to w.
6. Diagonal crease swapping x and w.

After those six, `Hello` sits here:

```text
w=0
  z=0
    y=0  . .
    y=1  l l
  z=1
    y=0  . o
    y=1  e H
```

Reading those vertices in the original numbering gives `lloeH`. `--legacy --map` draws the grid after every fold when the message fits in one tesseract. A multiscale map draws it after each pass. On a larger hypercube the grid is omitted. Either way the map follows selected symbols as `(x, y, z, w)`. A short message traces every filled vertex. A longer one traces the first four and the last, unless `--trace` names the indexes. The picture goes to standard error.

In legacy geometry a key is hashed with FNV-1a 64-bit. SplitMix64 draws a fold count from 4 to 7, then one catalog fold per count. The catalog has 32 folds, so five bits of each word pick one with no remainder. The same text and the same key always produce the same result. That plan can leave a run of characters in order. x is the fastest coordinate, so a key whose folds never touch x moves each group of S characters as a block. The block travels. The letters inside it do not.

Typed text and text files move Unicode code points, so `π` stays one symbol. `--binary` moves raw bytes and can split a UTF-8 sequence. Unfolding puts those bytes back. A file that is not UTF-8 is refused in text mode, and the message names `--binary`.

The working lists hold one vertex per symbol. Empty vertices of the larger hypercube are not stored, so a length just past 16, 256, 4096, or 65536 does not allocate that next grid. The time and memory follow the number of symbols. On one measurement, a canonical round trip of 4096 bytes and of 4097 bytes both took about 30 milliseconds and 0.4 MiB. At 65536 bytes both sides of the next boundary took about half a second and 8 MiB. A million bytes took about 9 seconds and 129 MiB, because each coordinate is a Python object. That suits documents and moderate binaries. It is not a fast general-purpose transformer.

## Multiscale geometry

The default fold is multiscale. One pass does four kinds of move, and every move is still one of the four isometries:

1. Fold the whole hypercube.
2. Fold each smaller block on its own. The block side runs from half the hypercube down to one tesseract.
3. Fold the arrangement of those blocks, so a block can trade places with another block.
4. Fold the whole hypercube again.

Each of those steps draws its own catalog folds from the key, the pass number, and a salt. If the draw misses an axis, it keeps drawing until x, y, z, and w have all taken part. Pass 2 does not repeat pass 1. `--passes` may be 1 to 16. One pass is the default, and on a long message it is enough to separate neighboring characters. Further passes cost time in proportion to the length.

This is still a rearrangement. It is not a random shuffle, and it is not encryption. The inverse is the same geometry run backwards, so the original comes back exactly.

`--legacy` keeps the older plan, so files folded before this change still open. `scramble` and `restore` in Python stay on that older plan as well. The command line does not, unless `--legacy` or `--folds` is set.

## Fold analysis

`--analyze` measures the permutation and still writes the folded result. The report goes to standard error. It gives the share of symbols that moved, the share left in place, the cycles, the longest cycle, and the order of the permutation. Unchanged positions are cycles of length 1 and are counted. For legacy geometry, each fold is measured against the arrangement before that fold, so a later fold that puts symbols back is visible.

Movement alone is a weak measure. A whole sentence can move and still be readable. The report therefore also counts neighboring symbols that stayed in their original order, the longest preserved run, how many original 8-character stretches survive as runs and as text, and the mean and farthest distance a symbol moved. A multiscale report repeats those measures after each pass.

For `Hello` and the canonical folds (`--legacy`) the report says that all five symbols moved, in one cycle of length 5, and that the order is 5. The first fold moves four of them. Folds 2, 3, and 4 leave that count at 80 percent. Fold 4 also returns one symbol to its start. The w mirror then drops the moved share to 60 percent and returns two symbols. The last crease moves all five. That mirror is the reversal the per-fold lines are there to show.

`--repeat` applies the same complete map until the original arrangement returns. For multiscale, one application is the whole set of passes, not one pass repeated. The count is the order of that permutation, the least common multiple of its cycle lengths. The program finds that count from the cycles and checks it by raising the permutation to that power. It does not walk a huge order one scramble at a time. When the order is at most 24 and the specimen is at most 48 symbols, it prints one line per application. `--legacy` on `Hello` returns on the fifth:

```text
application 0: Hello
application 1: lloeH
application 2: eoHll
application 3: lHloe
application 4: oleHl
application 5: Hello
```

`--repeat` and `--explore` print the report only. They do not write a folded file. `--length 16` runs either one with no document. `--explore --compare paper` asks whether two keys induce the same permutation of that length. Without `--legacy` or `--folds`, both sides are multiscale and use the same pass count. `--compare=` then compares with the empty key. `--compare-folds mx,mx` compares two legacy fold lists. Two different sequences can agree. Four `xy+` turns and two `mx` mirrors are both the identity on a filled tesseract, so the explorer reports `same permutation`.

## Files

Folding `note.txt` writes `note.tess.txt` beside it and leaves `note.txt` in place. Unfolding `note.tess.txt` writes `note.txt` when that path is free. A name with no `.tess` marker unfolds to `note.plain.txt`. Several files are each written beside themselves. A sibling that already exists is left untouched, and the program exits 1.

`--output` names one destination. It will not replace the input file, and `--force` does not change that. At a terminal it asks before replacing some other file that is already there. Answering anything other than `y` or `yes`, including end of file, leaves that file and exits 1. A pipe or a redirected command refuses the same replacement unless `--force` is set. `--force` replaces without asking.

A destination is written to a temporary file in the same folder, flushed, and then replaced. If the write fails, the temporary file is removed and the old destination stays as it was.

A file made without `--raw` starts with one plaintext line. Multiscale geometry uses version 4 and records the pass count. `--header --passes 2 Hello` begins:

```text
TESSERACT-FOLD/4 key=0 mode=text sha256=185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969 geometry=multiscale passes=2
```

Unfolding uses that count, so `--passes` is optional. A different count, or `--legacy` on a version 4 file, stops before anything is written. `--legacy` files stay on version 2:

```text
TESSERACT-FOLD/2 key=0 mode=text sha256=185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969
```

`key` is `1` when a phrase was used and `0` when it was not. The line does not contain the phrase. A custom `--folds` list uses version 3 and records the short names. `mx` on `Hello` begins:

```text
TESSERACT-FOLD/3 key=0 mode=text sha256=185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969 folds=mx
```

`#0` is stored as `xy+`. Unfolding a version 3 file uses that sequence, so `--folds` is optional. Passing a different list stops before anything is written. `--raw` leaves the sequence and the pass count out, and unfolding then needs the same `--folds` or `--passes` again. Versions 1, 2, and 3 are legacy geometry even when `--legacy` is omitted. `--passes` on one of those files is an error.

`mode` is `text` or `bin`. `sha256` is the SHA-256 digest of the original bytes. For text, that is the original UTF-8. Unfolding checks the digest after the symbols are restored and before anything is written. A mismatch means the key, the fold list, or the pass count is wrong, or the file was damaged. The digest is a corruption check, not an authenticity seal. A version 1 header has no digest and still unfolds:

```text
TESSERACT-FOLD/1 key=0 mode=text
```

A line that starts with `TESSERACT-FOLD/` and matches none of those forms is a damaged header. The program stops and writes nothing. `--raw` on unfold treats the whole input as payload, header included. A header that asks for a key, opened with no key, stops before the digest check.

Typed words and pipes omit the header unless `--header` is set. Calling `pack_document` without a digest still writes a version 1 header. The command line writes version 4 for multiscale geometry, version 2 for `--legacy`, and version 3 when `--folds` is set.

## Folders

A folder becomes one package. The tree is written into a zip archive with no compression, and that archive is folded as one binary message. `MyFolder` becomes `MyFolder.tess` beside it. `--folder MyFolder` does the same thing. `--file MyFolder` does too when `MyFolder` is a directory.

```bash
python3 tesseract_fold.py MyFolder --key paper
python3 tesseract_fold.py --decrypt MyFolder.tess --key paper --output MyFolder-restored
```

The package starts with `TESSERACT-FOLD-FOLDER/1`. That line records whether a key was used, the geometry, the pass count for multiscale geometry, the SHA-256 digest of the stored zip, and a custom `--folds` list when there is one. It does not record the key phrase. Unfolding reads the line, so `--passes`, `--legacy`, and `--folds` are not required again. A different pass count, or `--legacy` on a multiscale package, stops before any folder is created.

Restoring writes a new folder. The default name is the original folder name beside the package, which is usually already there, so pass `--output` to name a new folder. An existing folder is left in place. `--force` does not delete it. The archive's top directory is removed, so `--output` is the restored folder itself.

Files, nested directories, empty directories, and names such as `café.txt` come back as the same bytes. Symbolic links and special files are refused, and nothing is written. The source folder is not modified. The package has to sit outside the folder being packed. A path that escapes the archive, an absolute path, a second archive root, a compressed or encrypted member, or a declared size larger than the zip is rejected and no folder is created.

Timestamps, permissions, and ownership are not restored. A large folder costs the same as folding one file the size of the stored archive. This is not compression, and it is not a substitute for `AES_file`.

`--raw` on a package ignores the folder header and treats the file as an ordinary message. Folder mode does not combine with `--map`, `--analyze`, `--repeat`, `--explore`, `--header`, or `--binary`.

## Import

This directory is not a Python package. From this directory the functions can be called directly:

```python
from tesseract_fold import scramble, restore

scramble("Hello")                 # lloeH, legacy geometry
restore("lloeH")                  # Hello
scramble("Hello", "paper")        # oHell
scramble_multiscale("Hello")      # one multiscale pass
restore_multiscale("lelHo")       # Hello
restore(b"\x00\x01", "paper")     # bytes in, bytes out
```

`scramble` and `restore` stay on the legacy geometry so older programs keep their results. `scramble_multiscale` and `restore_multiscale` take a pass count, default 1. `parse_folds`, `format_analysis`, `format_repeat`, and `format_explore` are the same reports the command line prints. `format_analysis` defaults to legacy geometry. Pass `geometry="multiscale"` for the other report.

## Errors

`--help` and `-h` print the docstring and exit 0.

A bad argument prints `tesseract_fold.py:` and the usage line on standard error and exits 2. `--key` together with `--folds` is one of those. So is `--compare` without `--explore`, `--force` without `--output`, `--passes` together with `--legacy` or `--folds`, a pass count outside 1 to 16, `--folder` without a path, and folder mode combined with `--map`, `--analyze`, or `--check`.

A missing file, a file that is not UTF-8 in text mode, a key flag that does not match the header, a damaged header, a digest mismatch, a fold list that does not match a version 3 header, a pass count that does not match a version 4 header, `--legacy` on a version 4 file, a sibling that already exists, a declined replacement, or an existing `--output` file without `--force` or a yes at the terminal exits 1. The same exit is used when a folder contains a symlink or a special file, the package would be written inside that folder, the folder header is damaged, or the restore path already exists. `--force` does not replace a folder. The line starts with `tesseract_fold.py:`. Nothing partial is left behind.

Ctrl-C exits 130.

## Tests

From this folder:

```bash
python3 test_tesseract_fold.py
```

`python3 tesseract_fold.py --check` checks the geometry without the command-line cases: every catalog fold is a bijection on side 2 and side 4, the quarter-turns and mirrors have the right order, the canonical names parse back to the six folds, `Hello` folds to `lloeH`, the legacy plan for `Tim-the-tinkerer` still misses x, and a multiscale plan touches all four axes and round-trips.

The regression script also folds random bytes, Unicode, lengths on either side of 16, 256, and 4096, a wrong key, a damaged header, a version 1 file, a version 3 sequence that unfolds without being passed again, a version 4 pass count, a refused overwrite, and a write that fails before the destination is replaced. It packs a folder, restores the tree, and refuses a symlink, a package inside the source folder, and an existing restore path. `testdata/Creation.txt` is the permanent specimen for the key `Tim-the-tinkerer`: the legacy plan keeps long runs, and one multiscale pass does not.
