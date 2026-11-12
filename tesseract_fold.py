#!/usr/bin/env python3
"""Scramble or restore data by folding a tesseract.

Usage: tesseract_fold.py [--decrypt] [--key PHRASE] [--folds SPEC] [--legacy] [--passes N] [--file PATH] [--folder PATH] [--output PATH] [--force] [--binary] [--header] [--raw] [--map] [--trace INDEXES] [--analyze] [--repeat] [--explore] [--length N] [--compare PHRASE] [--compare-folds SPEC] [--text] [--menu] [--check] [TEXT | FILE]

A tesseract is a four-dimensional cube. It has 16 vertices, 32 edges,
24 square faces, and 8 cubic cells. This program sets each symbol on a
vertex of a hypercube grid, then folds that grid. A fold is an isometry
of the hypercube: a quarter-turn about two axes, a mirror through the
middle, a diagonal crease that swaps two axes, or a fold of one slab
back onto itself. The scrambled result is those same symbols read back
in coordinate order. Nothing is substituted. Only positions change.

The smallest grid is one tesseract: each axis is 0 or 1, and the 16
vertices are the points (x, y, z, w). A longer message uses the next
hypercube whose side is a power of two, so 16, 256, 4096, and so on.
Side 4 is a 2×2×2×2 packing of tesseracts. The side is chosen from the
length alone. Empty vertices hold nothing and do not appear in the result.

Coordinates are counted with x fastest: index i sits at
x = i mod S, y = (i // S) mod S, z = (i // S²) mod S, w = (i // S³) mod S.
After the folds, the symbols are read in that same order of their new
coordinates.

With --legacy and no key, every message takes the same six folds. The first four are
counterclockwise quarter-turns in the xy, zw, xz, and yw planes. A
quarter-turn in the plane of axes a and b sends a vertex (p, q) to
(S-1-q, p). That is the hinge that swings one cube of a tesseract net
about a square face. The fifth fold mirrors the hypercube through its
middle, perpendicular to w. The sixth creases it on the diagonal x = w
and swaps those axes. The same six folds restore nothing by themselves.
Decrypt with --decrypt.

In legacy geometry a key selects 4 to 7 folds. The phrase is hashed with FNV-1a 64-bit.
SplitMix64 draws one word for the count and one word per fold. Five bits
of each word pick a fold from a fixed catalog of 32. The same text and
the same key always produce the same result. A different key is a
different rearrangement. Encrypting the ciphertext again is not decrypting.

That key plan is legacy geometry. It can leave a run of characters in
their original order when none of the folds touch x, because x is the
fastest coordinate. Groups of S characters then move together. The
default is multiscale geometry. One pass folds the whole hypercube,
then each smaller block inside it, then the arrangement of those
blocks, and then the whole hypercube again. Every one of those steps
uses folds that touch x, y, z, and w. --passes N, from 1 to 16, derives
a different sequence for each pass from the key and the pass number.
The default is one pass. Repeating one sequence is a different
experiment: some folds undo each other, so --repeat measures that
return instead of stacking the same folds again.

--legacy keeps the older geometry. With no key that is the six folds
above, and Hello folds to lloeH. A key is the older 4 to 7 folds.
--folds is always that older geometry, in the order given. It cannot
be combined with --passes, and --passes cannot be combined with
--legacy.

This is obfuscation, the same kind of rearrangement as the dragon-curve
script. Anyone who can run the program and knows the key can reverse it.
It is not a substitute for AES_file.

Text words are joined with spaces. The printed line ends with a newline
that is not part of the result. A pipe keeps every character, including
newlines, and adds none. Typed text and text files move Unicode code
points, so a character stays a character. --binary moves raw bytes and
can tear a UTF-8 sequence apart; decrypting puts the bytes back.

--map traces the folds on standard error. The scrambled output is
unchanged. For one tesseract (16 symbols or fewer) the map draws the
vertices before the folds, after each fold, and at the end. It also
follows each chosen symbol through (x, y, z, w). On a larger hypercube
the grid is omitted and those paths are the picture. --trace 0,4
chooses write indexes. Without --trace, a short message shows every
filled vertex and a long one shows the first four and the last.

--analyze prints a fold report on standard error and still writes the
folded result. The report gives the share of symbols that moved, the
share left in place, the number of permutation cycles, the longest
cycle, and whether the permutation is the original arrangement. Each
fold has its own line, measured against the arrangement before that
fold, so a later fold that puts symbols back is visible. Unchanged
positions are cycles of length 1 and are included in the cycle count.
The report also counts neighboring symbols that stayed in their
original order, the longest preserved run, how many 8-character runs
survived, and how far symbols moved. Moving a whole sentence still
counts as moving every character. The neighbor count is what shows
that the sentence is still readable. A multiscale report adds those
measures after each pass.

--repeat applies that same complete sequence until the original
arrangement returns. That count is the order of the permutation, the
least common multiple of its cycle lengths. A short order is printed
one repetition per line. --length N runs the experiment on N symbols
when there is no message.

--folds SPEC chooses the folds and their order instead of a key. A
quarter-turn is xy+ or xy- (the other planes are xz, xw, yz, yw, and
zw). A mirror is mx, my, mz, or mw. A diagonal crease is dxy and the
same pattern for the other planes. A slab is hx- or hx+ (lower or
upper), and the same for y, z, and w. #0 through #31 pick a catalog
entry. Commas or spaces separate the names. The canonical six are
xy+,zw+,xz+,yw+,mw,dxw. --key and --folds cannot be combined. The same
list is required to unfold.

--explore reports the sequence, the cycles, and the order for a length.
It does not write a folded message. --compare PHRASE or
--compare-folds SPEC asks whether a second sequence is the same
permutation. With --legacy or --folds, --compare= compares with the
canonical folds. Otherwise it compares the same multiscale passes
with an empty key. The default length is 16, one tesseract.

A name that is an existing file is read as the message. note.txt is
written to note.tess.txt in the same folder. Decrypting note.tess.txt
writes note.txt when that path is free. A file made by this program
starts with a one-line header unless --raw is set. Version 2 records
the version, whether a key was used, whether the payload is text or
bytes, and the SHA-256 digest of the original bytes. It does not record
the key. A custom --folds list is recorded in a version 3 header, as
the short names of those folds, so unfolding that file does not need
--folds again. Version 4 records multiscale geometry and the pass
count, so unfolding does not need --passes again. The header selects
the geometry. --legacy on a version 4 file, or --passes on a legacy
file, or a pass count other than the one recorded, stops before
anything is written. Versions 1, 2, and 3 stay legacy. The sequence and
the pass count are not secrets. Unfolding checks the digest. A mismatch
means the key, the folds, or the pass count is wrong, or the file was
damaged. The digest is not an authenticity seal. Version 1 headers have
no digest and still unfold. Typed text and pipes omit the header unless
--header is set. Decrypt recognizes a header on its own. --raw while
decrypting means the whole input is payload, so a recorded sequence or
pass count is ignored and has to be passed again. A headerless legacy
result, including an older pipe of lloeH, needs --legacy to unfold.

--folder PATH stores a directory tree in one zip archive, without
compression, and folds that archive as one binary message. The package
is FolderName.tess beside the folder. A directory given as the message,
or as --file, is packed the same way. --decrypt of that package restores
the tree. The header records the geometry, the pass count, and any
custom folds, so those flags are not required again. An existing folder
is left in place. Symbolic links and special files are refused. The
files in the source folder are not modified.

The program writes a destination by finishing a temporary file in the
same folder and then replacing the destination. A failed write leaves
the old file in place and removes the temporary file. At a terminal,
--output asks before replacing a file that already exists. Anywhere
else it refuses, and the existing file stays, unless --force is set.
--force replaces without asking. --output will not replace the input
file, with or without --force. -- or --text before a name scrambles
the words themselves.

With no arguments at a terminal, a numbered menu opens. --menu opens it
explicitly. Folding asks for a pass count. Enter uses one multiscale
pass. The word legacy uses the older geometry. Unfolding a file follows
its header and does not ask. Choices 10 and 11 pack a folder and restore
it. A pipe is one exact message.

python3 tesseract_fold.py --legacy Hello
prints
lloeH

python3 tesseract_fold.py --help prints this text and exits 0.
"""

import hashlib
import math
import os
import re
import shlex
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

USAGE = (
    "usage: tesseract_fold.py [--decrypt] [--key PHRASE] [--folds SPEC] "
    "[--legacy] [--passes N] [--file PATH] [--folder PATH] [--output PATH] "
    "[--force] [--binary] [--header] [--raw] [--map] "
    "[--trace INDEXES] [--analyze] [--repeat] [--explore] [--length N] "
    "[--compare PHRASE] [--compare-folds SPEC] [--text] [--menu] [--check] "
    "[TEXT | FILE]"
)
NAME = "tesseract_fold.py"

# x, y, z, w. Index 0 is x and varies fastest when a vertex is numbered.
AXES = "xyzw"

# The six coordinate planes of four-dimensional space, in axis order.
PLANES = (
    (0, 1),  # xy
    (0, 2),  # xz
    (0, 3),  # xw
    (1, 2),  # yz
    (1, 3),  # yw
    (2, 3),  # zw
)

# FNV-1a 64-bit. The offset basis is also the hash of the empty byte string.
_FNV_OFFSET = 14695981039346656037
_FNV_PRIME = 1099511628211
_MASK64 = 0xFFFFFFFFFFFFFFFF

# A keyed message makes MIN_FOLDS to MIN_FOLDS + 3 folds.
MIN_FOLDS = 4

# Multiscale passes. Each pass derives its own folds from the key.
MAX_PASSES = 16

GEOMETRY_LEGACY = "legacy"
GEOMETRY_MULTISCALE = "multiscale"

# One tesseract has side 2. The next grids double the side.
MIN_SIDE = 2
MAX_SIDE = 256

# Header is plaintext and is never folded. The payload follows the newline.
# Version 1 has no digest. Version 2 stores SHA-256 of the original bytes.
# Version 3 also stores a custom fold sequence. Version 4 names multiscale
# geometry and the pass count. A key phrase is never stored.
HEADER_V1_RE = re.compile(rb"TESSERACT-FOLD/1 key=([01]) mode=(text|bin)\n")
HEADER_V2_RE = re.compile(
    rb"TESSERACT-FOLD/2 key=([01]) mode=(text|bin) sha256=([0-9a-f]{64})\n"
)
HEADER_V3_RE = re.compile(
    rb"TESSERACT-FOLD/3 key=0 mode=(text|bin) "
    rb"sha256=([0-9a-f]{64}) folds=([a-z0-9+#,.-]+)\n"
)
HEADER_V4_RE = re.compile(
    rb"TESSERACT-FOLD/4 key=([01]) mode=(text|bin) "
    rb"sha256=([0-9a-f]{64}) geometry=multiscale passes=([1-9][0-9]*)\n"
)
# A folder package is a stored zip folded as one message. The prefix is
# distinct from TESSERACT-FOLD/N so restore builds a tree, not a zip file.
FOLDER_HEADER_RE = re.compile(
    rb"TESSERACT-FOLD-FOLDER/1 key=([01]) geometry=(multiscale|legacy)"
    rb"(?: passes=([1-9][0-9]*))? sha256=([0-9a-f]{64}) bytes=([0-9]+)"
    rb"(?: folds=([a-z0-9+#,.-]+))?\n"
)
_NAME_MAX_BYTES = 255

# Repeated-fold listings stop after this many applications, and this width.
REPEAT_LIST_LIMIT = 24
REPEAT_WIDTH_LIMIT = 48
BAR_WIDTH = 20

# The unkeyed six folds, in the short names --folds accepts.
CANONICAL_SPEC = "xy+,zw+,xz+,yw+,mw,dxw"


def _catalog():
    """Thirty-two folds. Five key bits pick one, with no remainder.

    Twelve entries are quarter-turns (six planes, either way). Four are
    mirrors, one per axis. Six are diagonal creases. Eight fold a single
    slab. The last two repeat the xy quarter-turn and the w mirror so the
    catalog length is a power of two.
    """
    folds = []
    for axis_a, axis_b in PLANES:
        folds.append(("hinge", axis_a, axis_b, 1))
        folds.append(("hinge", axis_a, axis_b, 3))
    for axis in range(4):
        folds.append(("mirror", axis))
    for axis_a, axis_b in PLANES:
        folds.append(("diagonal", axis_a, axis_b))
    for axis in range(4):
        folds.append(("half", axis, 0))
        folds.append(("half", axis, 1))
    folds.append(("hinge", 0, 1, 1))
    folds.append(("mirror", 3))
    return tuple(folds)


CATALOG = _catalog()


def _fold_name_table():
    """Short names for the thirty distinct folds in the catalog."""
    names = {}
    for axis_a, axis_b in PLANES:
        plane = AXES[axis_a] + AXES[axis_b]
        names[plane + "+"] = ("hinge", axis_a, axis_b, 1)
        names[plane + "-"] = ("hinge", axis_a, axis_b, 3)
    for axis in range(4):
        names["m" + AXES[axis]] = ("mirror", axis)
    for axis_a, axis_b in PLANES:
        plane = AXES[axis_a] + AXES[axis_b]
        names["d" + plane] = ("diagonal", axis_a, axis_b)
    for axis in range(4):
        letter = AXES[axis]
        names["h" + letter + "-"] = ("half", axis, 0)
        names["h" + letter + "+"] = ("half", axis, 1)
    return names


FOLD_NAMES = _fold_name_table()


def _fold_by_value():
    """Map each distinct fold to the short name written in a header."""
    found = {}
    for name, fold in FOLD_NAMES.items():
        found.setdefault(fold, name)
    return found


FOLD_BY_VALUE = _fold_by_value()


def fold_spec(folds):
    """Return the comma-separated short names of a fold sequence.

    Catalog indexes are written as those names. ``#0`` becomes ``xy+``.
    """
    if isinstance(folds, str) or not isinstance(folds, (list, tuple)):
        raise TypeError("folds must be a list of folds")
    if not folds:
        raise ValueError("fold sequence is empty")
    names = []
    for fold in folds:
        name = FOLD_BY_VALUE.get(fold)
        if name is None:
            raise ValueError(f"unknown fold {fold!r}")
        names.append(name)
    return ",".join(names)


# The unkeyed trip: four hinges, then the w mirror, then the xw crease.
CANONICAL = (
    ("hinge", 0, 1, 1),
    ("hinge", 2, 3, 1),
    ("hinge", 0, 2, 1),
    ("hinge", 1, 3, 1),
    ("mirror", 3),
    ("diagonal", 0, 3),
)


def side_for(length):
    """Smallest power-of-two side whose hypercube has room for `length`."""
    if isinstance(length, bool) or not isinstance(length, int):
        raise TypeError("length must be an integer")
    if length < 0:
        raise ValueError("length must be non-negative")
    side = MIN_SIDE
    while side ** 4 < length:
        side *= 2
        if side > MAX_SIDE:
            raise ValueError(
                f"message is longer than a hypercube of side {MAX_SIDE}"
            )
    return side


def index_to_coord(index, side):
    """Return [x, y, z, w] for a vertex number. x varies fastest."""
    x = index % side
    y = (index // side) % side
    z = (index // side ** 2) % side
    w = (index // side ** 3) % side
    return [x, y, z, w]


def coord_to_index(coord, side):
    """Return the vertex number of an [x, y, z, w] coordinate."""
    return coord[0] + coord[1] * side + coord[2] * side ** 2 + coord[3] * side ** 3


def apply_fold(coord, fold, side):
    """Move one vertex by one fold. `coord` is updated in place.

    A hinge is a quarter-turn in a coordinate plane. In centered
    coordinates c = p - (S-1)/2, one counterclockwise turn sends
    (c_a, c_b) to (-c_b, c_a). On the grid that is
    (p_a, p_b) -> (S-1-p_b, p_a). Four turns restore the vertex.
    Three turns are one clockwise turn.

    A mirror reflects one axis through the middle of the hypercube:
    p -> (S-1-p). Two mirrors restore the vertex.

    A diagonal crease swaps two axes. Two creases restore the vertex.

    A half fold reflects inside one slab of thickness S/2 and leaves the
    other slab where it is. On a single tesseract each slab is one point
    thick, so a half fold does nothing there. Two half folds restore
    the vertex.
    """
    kind = fold[0]
    if kind == "hinge":
        _, axis_a, axis_b, turns = fold
        span = side - 1
        for _ in range(turns & 3):
            value_a = coord[axis_a]
            value_b = coord[axis_b]
            coord[axis_a] = span - value_b
            coord[axis_b] = value_a
        return
    if kind == "mirror":
        axis = fold[1]
        coord[axis] = side - 1 - coord[axis]
        return
    if kind == "diagonal":
        axis_a = fold[1]
        axis_b = fold[2]
        coord[axis_a], coord[axis_b] = coord[axis_b], coord[axis_a]
        return
    if kind == "half":
        axis = fold[1]
        upper = fold[2]
        mid = side // 2
        value = coord[axis]
        if upper:
            if value >= mid:
                coord[axis] = mid + (side - 1) - value
        elif value < mid:
            coord[axis] = (mid - 1) - value
        return
    raise ValueError(f"unknown fold {kind}")


def apply_folds(coord, folds, side):
    """Apply every fold in order to one vertex."""
    for fold in folds:
        apply_fold(coord, fold, side)


def fnv1a_64(data):
    """FNV-1a hash of data as an unsigned 64-bit integer."""
    digest = _FNV_OFFSET
    for byte in data:
        digest ^= byte
        digest = (digest * _FNV_PRIME) & _MASK64
    return digest


def splitmix64(state):
    """Advance a SplitMix64 state. Return (next state, output word)."""
    state = (state + 0x9E3779B97F4A7C15) & _MASK64
    word = state
    word = ((word ^ (word >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    word = ((word ^ (word >> 27)) * 0x94D049BB133111EB) & _MASK64
    return state, word ^ (word >> 31)


def fold_plan(key):
    """Return the folds for a key.

    An empty key is the six canonical folds. Any other key is 4 to 7
    catalog folds drawn from the key's hash by SplitMix64.
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    if key == "":
        return CANONICAL
    state, word = splitmix64(fnv1a_64(key.encode("utf-8")))
    count = MIN_FOLDS + (word >> 62)
    folds = []
    for _ in range(count):
        state, word = splitmix64(state)
        folds.append(CATALOG[word & 31])
    return tuple(folds)


def axes_of(fold):
    """The coordinate axes one fold touches."""
    kind = fold[0]
    if kind in ("hinge", "diagonal"):
        return fold[1], fold[2]
    if kind in ("mirror", "half"):
        return (fold[1],)
    raise ValueError(f"unknown fold {kind}")


def fold_plan_mixed(key, pass_index=0, salt="global"):
    """Return 4 or more catalog folds that touch every axis.

    The draw is SplitMix64, as in fold_plan. The hashed text is the salt,
    the pass number, and the key, so each pass and each scale differs.
    A draw that misses an axis keeps going until that axis appears.
    This is not the legacy key plan. Old files still use fold_plan.
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    if isinstance(pass_index, bool) or not isinstance(pass_index, int):
        raise TypeError("pass index must be an integer")
    if pass_index < 0:
        raise ValueError("pass index must be non-negative")
    if not isinstance(salt, str):
        raise TypeError("salt must be a string")
    # The pass number is decimal text, with NUL separators, so pass 0 and
    # pass 1 cannot collide with a salt or a key that contains digits.
    material = f"{salt}\0{pass_index}\0{key}".encode("utf-8")
    state, word = splitmix64(fnv1a_64(material))
    count = MIN_FOLDS + (word >> 62)
    folds = []
    covered = set()
    for _ in range(count):
        state, word = splitmix64(state)
        fold = CATALOG[word & 31]
        folds.append(fold)
        covered.update(axes_of(fold))
    for axis in range(4):
        if axis in covered:
            continue
        while True:
            state, word = splitmix64(state)
            fold = CATALOG[word & 31]
            if axis in axes_of(fold):
                folds.append(fold)
                covered.update(axes_of(fold))
                break
    return tuple(folds)


def inverse_fold(fold):
    """The fold that undoes one catalog fold."""
    if fold[0] == "hinge":
        return (fold[0], fold[1], fold[2], (-fold[3]) & 3)
    return fold


def inverse_folds(folds):
    """Undo a sequence by reversing it and inverting each fold."""
    return tuple(inverse_fold(fold) for fold in reversed(folds))


def _pass_steps(key, pass_index, side):
    """Global folds, then local and coarse folds at each smaller scale.

    Scales run from the half-side down to a single tesseract. A local
    fold moves coordinates inside each block. A coarse fold moves the
    blocks. x is the fast axis, so a local fold is what breaks a run of
    neighboring symbols.
    """
    steps = [("global", fold_plan_mixed(key, pass_index, "global-a"), side)]
    scale = side // 2
    while scale >= MIN_SIDE:
        steps.append(("local", fold_plan_mixed(key, pass_index, f"local-{scale}"), scale))
        steps.append(("coarse", fold_plan_mixed(key, pass_index, f"coarse-{scale}"), scale))
        scale //= 2
    steps.append(("global", fold_plan_mixed(key, pass_index, "global-b"), side))
    return steps


def _apply_step(coords, kind, folds, scale, side):
    """Apply one multiscale step to every occupied coordinate."""
    if kind == "global":
        for coord in coords:
            apply_folds(coord, folds, side)
        return
    if kind == "local":
        for coord in coords:
            region = [value // scale for value in coord]
            local = [value % scale for value in coord]
            apply_folds(local, folds, scale)
            for axis in range(4):
                coord[axis] = region[axis] * scale + local[axis]
        return
    coarse_side = side // scale
    for coord in coords:
        local = [value % scale for value in coord]
        region = [value // scale for value in coord]
        apply_folds(region, folds, coarse_side)
        for axis in range(4):
            coord[axis] = region[axis] * scale + local[axis]


def _check_passes(passes):
    """Reject a pass count outside 1..MAX_PASSES."""
    if isinstance(passes, bool) or not isinstance(passes, int):
        raise TypeError("passes must be an integer")
    if not 1 <= passes <= MAX_PASSES:
        raise ValueError(f"passes must be from 1 to {MAX_PASSES}")


def _pass_count_text(passes):
    """`1 pass` or `2 passes`."""
    noun = "pass" if passes == 1 else "passes"
    return f"{passes} {noun}"


def _multiscale_coords(length, key, passes):
    """Return coordinates after every multiscale pass, and the side."""
    _check_passes(passes)
    side = side_for(length)
    coords = [index_to_coord(index, side) for index in range(length)]
    frames = []
    for pass_index in range(passes):
        for kind, folds, scale in _pass_steps(key, pass_index, side):
            _apply_step(coords, kind, folds, scale, side)
        frames.append([tuple(coord) for coord in coords])
    return frames, side


def multiscale_pass_ranks(length, key="", passes=1):
    """Return the read-position map after each multiscale pass."""
    frames, side = _multiscale_coords(length, key, passes)
    ranks = []
    for frame in frames:
        vertices = [coord_to_index(coord, side) for coord in frame]
        ranks.append(_ranks_from_vertices(vertices))
    return ranks


def multiscale_ranks(length, key="", passes=1):
    """Return dest for one multiscale fold of `passes` passes."""
    ranks = multiscale_pass_ranks(length, key, passes)
    if not ranks:
        return list(range(length))
    return ranks[-1]


def describe_fold(fold):
    """One short line naming a fold in ordinary geometric language."""
    kind = fold[0]
    if kind == "hinge":
        _, axis_a, axis_b, turns = fold
        sense = "counterclockwise" if turns == 1 else "clockwise"
        plane = AXES[axis_a] + AXES[axis_b]
        return f"quarter-turn {sense} in the {plane} plane"
    if kind == "mirror":
        return f"mirror through the middle, perpendicular to {AXES[fold[1]]}"
    if kind == "diagonal":
        plane = AXES[fold[1]] + AXES[fold[2]]
        return f"diagonal crease swapping {plane[0]} and {plane[1]}"
    if kind == "half":
        slab = "upper" if fold[2] else "lower"
        return f"fold the {slab} {AXES[fold[1]]} slab back on itself"
    raise ValueError(f"unknown fold {kind}")


def describe_plan(key):
    """Name every fold of a key, one fold per line after the count."""
    folds = fold_plan(key)
    lines = [f"{len(folds)} fold(s)"]
    for number, fold in enumerate(folds, start=1):
        lines.append(f"  {number}. {describe_fold(fold)}")
    return "\n".join(lines)


def _ranks_from_vertices(vertices):
    """Turn folded vertex numbers into read positions.

    dest[i] is where the symbol written at i is read. One integer list
    is sorted by index, instead of a list of coordinate tuples.
    """
    length = len(vertices)
    order = sorted(range(length), key=vertices.__getitem__)
    dest = [0] * length
    previous = None
    for rank, source in enumerate(order):
        vertex = vertices[source]
        if vertex == previous:
            raise RuntimeError("fold sent two symbols to one vertex")
        previous = vertex
        dest[source] = rank
    return dest


def destination_ranks(length, folds):
    """Return dest such that output[dest[i]] is the symbol written at i.

    Each written vertex is folded, then the occupied vertices are sorted
    by their new vertex numbers. dest[i] is where symbol i is read.
    Two symbols never land on one vertex, because every fold is a
    bijection of the grid and a composition of bijections is a bijection.
    """
    if isinstance(length, bool) or not isinstance(length, int):
        raise TypeError("length must be an integer")
    if length < 0:
        raise ValueError("length must be non-negative")
    side = side_for(length)
    vertices = [0] * length
    for index in range(length):
        coord = index_to_coord(index, side)
        apply_folds(coord, folds, side)
        vertices[index] = coord_to_index(coord, side)
    return _ranks_from_vertices(vertices)


def active_folds(key="", folds=None):
    """Return the fold tuple a key or an explicit list selects."""
    if folds is not None:
        return tuple(folds)
    return fold_plan(key)


def _rearrange(items, key, decrypting, folds=None):
    """Permute a str or a bytes object. The type is preserved."""
    if isinstance(items, str):
        symbols = list(items)
    elif isinstance(items, (bytes, bytearray)):
        symbols = list(items)
    else:
        raise TypeError("data must be a string or bytes")
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    chosen = active_folds(key, folds)
    dest = destination_ranks(len(symbols), chosen)
    if decrypting:
        symbols = [symbols[dest[index]] for index in range(len(symbols))]
    elif isinstance(items, (bytes, bytearray)):
        out = bytearray(len(symbols))
        for index, symbol in enumerate(symbols):
            out[dest[index]] = symbol
        return bytes(out)
    else:
        out = [None] * len(symbols)
        for index, symbol in enumerate(symbols):
            out[dest[index]] = symbol
        symbols = out
    if isinstance(items, str):
        return "".join(symbols)
    return bytes(symbols)


def scramble(items, key="", folds=None):
    """Fold items. `key` is a phrase, or "" for the canonical folds.

    `folds` replaces the key. Pass the same list to restore.
    """
    return _rearrange(items, key, False, folds)


def restore(items, key="", folds=None):
    """Undo scramble(items, key, folds). The same folds are required."""
    return _rearrange(items, key, True, folds)


def scramble_multiscale(items, key="", passes=1):
    """Fold items with multiscale geometry. `passes` uses a new plan each time."""
    return _rearrange_multiscale(items, key, passes, False)


def restore_multiscale(items, key="", passes=1):
    """Undo scramble_multiscale(items, key, passes)."""
    return _rearrange_multiscale(items, key, passes, True)


def _rearrange_multiscale(items, key, passes, decrypting):
    """Permute a str or bytes by the multiscale map. The type is preserved."""
    if isinstance(items, str):
        symbols = list(items)
    elif isinstance(items, (bytes, bytearray)):
        symbols = list(items)
    else:
        raise TypeError("data must be a string or bytes")
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    dest = multiscale_ranks(len(symbols), key, passes)
    if decrypting:
        symbols = [symbols[dest[index]] for index in range(len(symbols))]
    elif isinstance(items, (bytes, bytearray)):
        out = bytearray(len(symbols))
        for index, symbol in enumerate(symbols):
            out[dest[index]] = symbol
        return bytes(out)
    else:
        out = [None] * len(symbols)
        for index, symbol in enumerate(symbols):
            out[dest[index]] = symbol
        symbols = out
    if isinstance(items, str):
        return "".join(symbols)
    return bytes(symbols)


def parse_folds(spec):
    """Parse a fold list such as ``xy+,mw,hx+`` or ``#0,#12``.

    Commas and whitespace separate names. Letter case does not matter.
    """
    if not isinstance(spec, str):
        raise TypeError("fold sequence must be a string")
    parts = [part for part in re.split(r"[\s,]+", spec.strip()) if part]
    if not parts:
        raise ValueError("fold sequence is empty")
    folds = []
    for part in parts:
        name = part.lower()
        if name.startswith("#"):
            number = name[1:]
            if not number.isdigit() or int(number) >= len(CATALOG):
                raise ValueError(f"unknown fold {part}")
            folds.append(CATALOG[int(number)])
            continue
        if name not in FOLD_NAMES:
            raise ValueError(f"unknown fold {part}")
        folds.append(FOLD_NAMES[name])
    return tuple(folds)


def fold_legend():
    """The short names accepted by --folds, in catalog order."""
    turns = " ".join(plane + sign for plane in (
        "xy", "xz", "xw", "yz", "yw", "zw"
    ) for sign in ("+", "-"))
    return "\n".join((
        "Quarter-turns: " + turns,
        "Mirrors: mx my mz mw",
        "Diagonals: dxy dxz dxw dyz dyw dzw",
        "Slabs: hx- hx+ hy- hy+ hz- hz+ hw- hw+",
        "Catalog index: #0 through #31",
        "Canonical: " + CANONICAL_SPEC,
    ))


def describe_folds(folds):
    """Name every fold, one fold per line after the count."""
    lines = [f"{len(folds)} fold(s)"]
    for number, fold in enumerate(folds, start=1):
        lines.append(f"  {number}. {describe_fold(fold)}")
    return "\n".join(lines)


def _cycle_lengths(dest):
    """Return the length of every cycle, including fixed points."""
    seen = [False] * len(dest)
    lengths = []
    for start in range(len(dest)):
        if seen[start]:
            continue
        length = 0
        index = start
        while not seen[index]:
            seen[index] = True
            index = dest[index]
            length += 1
        lengths.append(length)
    return lengths


def permutation_order(dest):
    """Return (order, cycle lengths).

    The order is the least common multiple of the cycle lengths. Applying
    the permutation that many times restores every position.
    """
    lengths = _cycle_lengths(dest)
    order = 1
    for length in lengths:
        order = math.lcm(order, length)
    return order, lengths


def permute_power(dest, exponent):
    """Where each symbol sits after `exponent` applications of dest.

    dest[i] is the position of the symbol that started at i. The result
    uses the same convention. Exponent 0 is the original arrangement.
    """
    if exponent < 0:
        raise ValueError("exponent must be non-negative")
    result = list(range(len(dest)))
    base = list(dest)
    power = exponent
    while power:
        if power & 1:
            result = [base[index] for index in result]
        if power > 1:
            base = [base[index] for index in base]
        power >>= 1
    return result


def permutation_stats(dest):
    """Summarize a permutation of positions 0 .. n-1."""
    lengths = _cycle_lengths(dest)
    unchanged = lengths.count(1)
    length = len(dest)
    moved = length - unchanged
    longest = max(lengths) if lengths else 0
    order, _same = permutation_order(dest)
    return {
        "length": length,
        "moved": moved,
        "unchanged": unchanged,
        "cycles": len(lengths),
        "longest": longest,
        "lengths": lengths,
        "order": order,
        "identity": moved == 0,
    }


def analyze_sequence(length, folds):
    """Return (steps, final) for the cumulative permutation.

    steps[k] describes the arrangement after fold k. ``change`` is
    ``increased``, ``reversed``, or ``unchanged`` compared with the
    number of symbols away from their start before that fold.
    ``returned`` counts symbols that were away and are home again.
    """
    side = side_for(length)
    coords = [index_to_coord(index, side) for index in range(length)]
    previous = list(range(length))
    previous_moved = 0
    steps = []
    for fold in folds:
        for coord in coords:
            apply_fold(coord, fold, side)
        vertices = [coord_to_index(coord, side) for coord in coords]
        dest = _ranks_from_vertices(vertices)
        stats = permutation_stats(dest)
        returned = 0
        for index in range(length):
            if previous[index] != index and dest[index] == index:
                returned += 1
        if stats["moved"] > previous_moved:
            change = "increased"
        elif stats["moved"] < previous_moved:
            change = "reversed"
        else:
            change = "unchanged"
        stats["returned"] = returned
        stats["change"] = change
        stats["fold"] = fold
        steps.append(stats)
        previous = dest
        previous_moved = stats["moved"]
    if steps:
        final = permutation_stats(previous)
    else:
        final = permutation_stats(list(range(length)))
    return steps, final


def _pct(part, whole):
    if whole == 0:
        return "0.0%"
    return f"{(100.0 * part / whole):.1f}%"


def _bar(part, whole):
    if whole == 0:
        filled = 0
    else:
        filled = int(round(BAR_WIDTH * part / whole))
        if part and filled == 0:
            filled = 1
        if part < whole and filled == BAR_WIDTH:
            filled = BAR_WIDTH - 1
    return "#" * filled + "." * (BAR_WIDTH - filled)


def _cycle_phrase(lengths):
    if not lengths:
        return "0 cycles, longest 0"
    ordered = sorted(lengths, reverse=True)
    shown = ", ".join(str(number) for number in ordered[:12])
    if len(ordered) > 12:
        shown += f", and {len(ordered) - 12} more"
    longest = ordered[0]
    return (
        f"{len(lengths)} cycles, longest {longest}\n"
        f"lengths {shown}"
    )


def _change_phrase(step):
    change = step["change"]
    returned = step["returned"]
    if change == "increased":
        line = "displacement increased"
    elif change == "reversed":
        line = "reversed some earlier displacement"
    else:
        line = "displacement unchanged"
    if returned:
        noun = "symbol" if returned == 1 else "symbols"
        line += f" ({returned} {noun} returned to the start)"
    return line


def preserved_runs(dest):
    """Lengths of runs whose symbols stayed in their original order.

    A run of length 1 is a symbol whose successor did not follow it.
    Neighboring positions i and i+1 stay together when dest[i+1] is
    dest[i] + 1.
    """
    length = len(dest)
    if length == 0:
        return []
    runs = []
    start = 0
    for index in range(length - 1):
        if dest[index + 1] != dest[index] + 1:
            runs.append(index + 1 - start)
            start = index + 1
    runs.append(length - start)
    return runs


def windows_in_runs(runs, width):
    """How many windows of `width` sit inside preserved runs."""
    return sum(max(0, run - width + 1) for run in runs)


def surviving_text_windows(original, folded, width):
    """How many original windows of `width` still occur in `folded`.

    Each starting position in the original is counted once, even when
    the same text occurs more than once.
    """
    if len(original) < width or len(folded) < width:
        return 0
    found = {
        folded[index:index + width]
        for index in range(len(folded) - width + 1)
    }
    return sum(
        1
        for index in range(len(original) - width + 1)
        if original[index:index + width] in found
    )


def _apply_dest(symbols, dest):
    """Place symbols at their read positions."""
    out = [None] * len(symbols)
    for index, symbol in enumerate(symbols):
        out[dest[index]] = symbol
    if symbols and isinstance(symbols[0], int) and not isinstance(symbols, str):
        return bytes(out)
    if isinstance(symbols, (bytes, bytearray)):
        return bytes(out)
    return "".join(out)


def format_quality(dest, symbols=None):
    """Lines describing whether original order survived the permutation."""
    length = len(dest)
    runs = preserved_runs(dest)
    pairs = max(length - 1, 0)
    adjacent = sum(run - 1 for run in runs)
    longest = max(runs) if runs else 0
    if length:
        moved = [abs(dest[index] - index) for index in range(length)]
        mean = sum(moved) / length
        farthest = max(moved)
    else:
        mean = 0.0
        farthest = 0
    lines = [
        "Scramble quality",
        (
            f"{_pct(adjacent, pairs)} of neighboring pairs stayed in order "
            f"({adjacent} of {pairs})"
        ),
        f"longest preserved sequence {longest}",
        f"preserved 8-character runs {windows_in_runs(runs, 8)}",
    ]
    if symbols is not None:
        folded = _apply_dest(symbols, dest)
        original = bytes(symbols) if isinstance(symbols, (bytes, bytearray)) else symbols
        lines.append(
            "surviving 8-character text windows "
            f"{surviving_text_windows(original, folded, 8)}"
        )
    lines.append(f"mean displacement {mean:.1f} symbols, farthest {farthest}")
    return lines


def _quality_symbols(items):
    """The symbol sequence quality can search, or None for a bare length."""
    if isinstance(items, str):
        return items
    if isinstance(items, (bytes, bytearray)):
        return bytes(items)
    return None


def format_multiscale_analysis(items, key="", passes=1):
    """Report multiscale folds, including whether order survived each pass."""
    if isinstance(items, int) and not isinstance(items, bool):
        length = items
        title = f"{length} symbols"
    elif isinstance(items, (str, bytes, bytearray)):
        length = len(items)
        kind = "bytes" if isinstance(items, (bytes, bytearray)) else "symbols"
        title = f"{length} {kind}"
    else:
        raise TypeError("analysis needs a string, bytes, or a length")
    _check_passes(passes)
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    side = side_for(length)
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}, {side ** 4} vertices"
    ranks = multiscale_pass_ranks(length, key, passes)
    final_dest = ranks[-1] if ranks else list(range(length))
    final = permutation_stats(final_dest)
    if final["identity"]:
        arrangement = "the permutation is the original arrangement"
    else:
        arrangement = "the permutation is not the original arrangement"
    lines = [
        "FOLD ANALYSIS",
        f"{title} on {figure}",
        f"multiscale geometry, {_pass_count_text(passes)}",
        "Each pass folds the whole hypercube, then the blocks inside it,",
        "then the arrangement of those blocks, then the whole hypercube again.",
        "",
        f"{_pct(final['moved'], length)} moved ({final['moved']} of {length})",
        (
            f"{_pct(final['unchanged'], length)} unchanged "
            f"({final['unchanged']} of {length})"
        ),
        _cycle_phrase(final["lengths"]),
        f"order {final['order']}",
        arrangement,
        "Unchanged positions are cycles of length 1 and are included above.",
        "",
    ]
    for pass_index in range(passes):
        lines.append(f"Pass {pass_index + 1}")
        for kind, folds, scale in _pass_steps(key, pass_index, side):
            if kind == "global":
                label = "whole hypercube"
            elif kind == "local":
                label = f"blocks of side {scale}"
            else:
                label = f"arrange blocks of side {scale}"
            lines.append(f"  {label}: {fold_spec(folds)}")
        lines.append("")
    lines.extend(format_quality(final_dest, _quality_symbols(items)))
    lines.append("")
    lines.append("After each pass")
    symbols = _quality_symbols(items)
    for pass_index, dest in enumerate(ranks, start=1):
        runs = preserved_runs(dest)
        pairs = max(length - 1, 0)
        adjacent = sum(run - 1 for run in runs)
        longest = max(runs) if runs else 0
        if length:
            mean = sum(abs(dest[index] - index) for index in range(length)) / length
        else:
            mean = 0.0
        text_windows = ""
        if symbols is not None:
            folded = _apply_dest(symbols, dest)
            original = bytes(symbols) if isinstance(symbols, (bytes, bytearray)) else symbols
            text_windows = (
                ", surviving 8-character text "
                f"{surviving_text_windows(original, folded, 8)}"
            )
        lines.append(
            f"  pass {pass_index:<2}  neighboring pairs {_pct(adjacent, pairs)}"
            f", longest {longest}"
            f", preserved 8-character runs {windows_in_runs(runs, 8)}"
            f"{text_windows}"
            f", mean displacement {mean:.1f}"
        )
    return "\n".join(lines)


def format_analysis(items, key="", folds=None, geometry=GEOMETRY_LEGACY, passes=1):
    """Report how the folds permute a message or a length."""
    if geometry == GEOMETRY_MULTISCALE and folds is None:
        return format_multiscale_analysis(items, key, passes)
    if isinstance(items, int) and not isinstance(items, bool):
        length = items
        title = f"{length} symbols"
    elif isinstance(items, (str, bytes, bytearray)):
        length = len(items)
        kind = "bytes" if isinstance(items, (bytes, bytearray)) else "symbols"
        title = f"{length} {kind}"
    else:
        raise TypeError("analysis needs a string, bytes, or a length")
    chosen = active_folds(key, folds)
    side = side_for(length)
    steps, final = analyze_sequence(length, chosen)
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}, {side ** 4} vertices"
    if final["identity"]:
        arrangement = "the permutation is the original arrangement"
    else:
        arrangement = "the permutation is not the original arrangement"
    lines = [
        "FOLD ANALYSIS",
        f"{title} on {figure}",
        describe_folds(chosen),
        "",
        f"{_pct(final['moved'], length)} moved ({final['moved']} of {length})",
        (
            f"{_pct(final['unchanged'], length)} unchanged "
            f"({final['unchanged']} of {length})"
        ),
        _cycle_phrase(final["lengths"]),
        f"order {final['order']}",
        arrangement,
        "Unchanged positions are cycles of length 1 and are included above.",
        "",
        "Symbol movement after each fold",
        f"  start  {_pct(0, length):>6}  {_bar(0, length)}",
    ]
    for number, step in enumerate(steps, start=1):
        lines.append(
            f"  {number:<5}  {_pct(step['moved'], length):>6}  {_bar(step['moved'], length)}"
        )
        lines.append(f"         {describe_fold(step['fold'])}")
        lines.append(f"         {_change_phrase(step)}")
    lines.append("")
    lines.extend(format_quality(destination_ranks(length, chosen), _quality_symbols(items)))
    return "\n".join(lines)


def same_permutation(length, folds_a, folds_b):
    """True when two fold lists move a message of this length the same way."""
    return destination_ranks(length, folds_a) == destination_ranks(length, folds_b)


def _one_line(items):
    """Show a specimen as a single line."""
    if isinstance(items, (bytes, bytearray)):
        if len(items) > 24:
            return f"{len(items)} bytes"
        return items.hex(" ")
    text = items.replace("\\", "\\\\")
    return (
        text.replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def format_repeat(items, key="", folds=None, geometry=GEOMETRY_LEGACY, passes=1):
    """Report how many repetitions restore this arrangement."""
    if geometry == GEOMETRY_MULTISCALE and folds is None:
        return _format_multiscale_repeat(items, key, passes)
    chosen = active_folds(key, folds)
    tokens = None
    if isinstance(items, bool):
        raise TypeError("repeat needs a string, bytes, or a length")
    if isinstance(items, int):
        length = items
        if 0 < length <= 26:
            tokens = "abcdefghijklmnopqrstuvwxyz"[:length]
        label = f"{length} symbols"
    elif isinstance(items, (str, bytes, bytearray)):
        length = len(items)
        tokens = items
        label = (
            f"{length} bytes"
            if isinstance(items, (bytes, bytearray))
            else f"{length} symbols"
        )
    else:
        raise TypeError("repeat needs a string, bytes, or a length")
    side = side_for(length)
    dest = destination_ranks(length, chosen)
    order, lengths = permutation_order(dest)
    if permute_power(dest, order) != list(range(length)):
        raise RuntimeError("permutation order did not restore the arrangement")
    if order > 1 and permute_power(dest, order - 1) == list(range(length)):
        raise RuntimeError("permutation order is not the first return")
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}"
    lines = [
        "REPEATED FOLD",
        f"{label} on {figure}",
        "The same sequence is applied until the original arrangement returns.",
        describe_folds(chosen),
        "",
        f"order {order}",
        _cycle_phrase(lengths),
    ]
    if order == 1:
        lines.append("One application already leaves the original arrangement.")
    else:
        lines.append(f"The arrangement returns after {order} applications.")
    show = (
        tokens is not None
        and order <= REPEAT_LIST_LIMIT
        and length <= REPEAT_WIDTH_LIMIT
    )
    if show:
        lines.append("")
        lines.append("Each line applies the whole sequence once.")
        current = tokens
        lines.append(f"application 0: {_one_line(current)}")
        for number in range(1, order + 1):
            current = scramble(current, folds=chosen)
            lines.append(f"application {number}: {_one_line(current)}")
        if current != tokens:
            raise RuntimeError("repeated folds did not restore the specimen")
    else:
        lines.append("The order is the least common multiple of the cycle lengths.")
        if order > REPEAT_LIST_LIMIT or length > REPEAT_WIDTH_LIMIT:
            lines.append("That return is too long to print one line per repetition.")
    return "\n".join(lines)


def _format_multiscale_repeat(items, key, passes):
    """Report the order of one whole multiscale map."""
    _check_passes(passes)
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    tokens = None
    if isinstance(items, bool):
        raise TypeError("repeat needs a string, bytes, or a length")
    if isinstance(items, int):
        length = items
        if 0 < length <= 26:
            tokens = "abcdefghijklmnopqrstuvwxyz"[:length]
        label = f"{length} symbols"
    elif isinstance(items, (str, bytes, bytearray)):
        length = len(items)
        tokens = items
        label = (
            f"{length} bytes"
            if isinstance(items, (bytes, bytearray))
            else f"{length} symbols"
        )
    else:
        raise TypeError("repeat needs a string, bytes, or a length")
    side = side_for(length)
    dest = multiscale_ranks(length, key, passes)
    order, lengths = permutation_order(dest)
    if permute_power(dest, order) != list(range(length)):
        raise RuntimeError("permutation order did not restore the arrangement")
    if order > 1 and permute_power(dest, order - 1) == list(range(length)):
        raise RuntimeError("permutation order is not the first return")
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}"
    lines = [
        "REPEATED FOLD",
        f"{label} on {figure}",
        "The whole multiscale map is applied until the original arrangement returns.",
        f"multiscale geometry, {_pass_count_text(passes)}",
        "Each pass derives its own folds from the key and the pass number.",
        "",
        f"order {order}",
        _cycle_phrase(lengths),
    ]
    if order == 1:
        lines.append("One application already leaves the original arrangement.")
    else:
        lines.append(f"The arrangement returns after {order} applications.")
    show = (
        tokens is not None
        and order <= REPEAT_LIST_LIMIT
        and length <= REPEAT_WIDTH_LIMIT
    )
    if show:
        lines.append("")
        lines.append("Each line applies the whole multiscale map once.")
        current = tokens
        lines.append(f"application 0: {_one_line(current)}")
        for number in range(1, order + 1):
            current = scramble_multiscale(current, key, passes)
            lines.append(f"application {number}: {_one_line(current)}")
        if current != tokens:
            raise RuntimeError("repeated folds did not restore the specimen")
    else:
        lines.append("The order is the least common multiple of the cycle lengths.")
        if order > REPEAT_LIST_LIMIT or length > REPEAT_WIDTH_LIMIT:
            lines.append("That return is too long to print one line per repetition.")
    return "\n".join(lines)


def format_explore(length, folds, other=None, other_label="the other sequence"):
    """Describe one permutation, and optionally compare it with a second."""
    if isinstance(length, bool) or not isinstance(length, int):
        raise TypeError("length must be an integer")
    if length < 0:
        raise ValueError("length must be non-negative")
    side = side_for(length)
    _steps, final = analyze_sequence(length, folds)
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}, {side ** 4} vertices"
    lines = [
        "PERMUTATION EXPLORER",
        f"length {length}, {figure}",
    ]
    if length == side ** 4:
        lines.append("This length fills the hypercube.")
    lines.extend((
        "",
        "Sequence",
        describe_folds(folds),
        "",
        f"{_pct(final['moved'], length)} moved ({final['moved']} of {length})",
        f"{_pct(final['unchanged'], length)} unchanged ({final['unchanged']} of {length})",
        _cycle_phrase(final["lengths"]),
        f"order {final['order']}",
        (
            "the permutation is the original arrangement"
            if final["identity"]
            else "the permutation is not the original arrangement"
        ),
    ))
    if other is not None:
        _other_steps, second = analyze_sequence(length, other)
        lines.extend((
            "",
            other_label[0].upper() + other_label[1:],
            describe_folds(other),
            "",
            f"order {second['order']}",
            _cycle_phrase(second["lengths"]),
            "",
            (
                "same permutation"
                if same_permutation(length, folds, other)
                else "different permutation"
            ),
        ))
    return "\n".join(lines)


def format_multiscale_explore(length, key="", passes=1, other_key=None, other_label="the other key"):
    """Describe a multiscale permutation, and optionally compare a second key."""
    if isinstance(length, bool) or not isinstance(length, int):
        raise TypeError("length must be an integer")
    if length < 0:
        raise ValueError("length must be non-negative")
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    _check_passes(passes)
    side = side_for(length)
    final = permutation_stats(multiscale_ranks(length, key, passes))
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}, {side ** 4} vertices"
    lines = [
        "PERMUTATION EXPLORER",
        f"length {length}, {figure}",
    ]
    if length == side ** 4:
        lines.append("This length fills the hypercube.")
    lines.extend((
        "",
        "Sequence",
        f"multiscale geometry, {_pass_count_text(passes)}",
        "Each pass derives its own folds from the key and the pass number.",
        "",
        f"{_pct(final['moved'], length)} moved ({final['moved']} of {length})",
        f"{_pct(final['unchanged'], length)} unchanged ({final['unchanged']} of {length})",
        _cycle_phrase(final["lengths"]),
        f"order {final['order']}",
        (
            "the permutation is the original arrangement"
            if final["identity"]
            else "the permutation is not the original arrangement"
        ),
    ))
    if other_key is not None:
        if not isinstance(other_key, str):
            raise TypeError("key must be a string")
        second = permutation_stats(multiscale_ranks(length, other_key, passes))
        same = multiscale_ranks(length, key, passes) == multiscale_ranks(length, other_key, passes)
        lines.extend((
            "",
            other_label[0].upper() + other_label[1:],
            f"multiscale geometry, {_pass_count_text(passes)}",
            "",
            f"order {second['order']}",
            _cycle_phrase(second["lengths"]),
            "",
            "same permutation" if same else "different permutation",
        ))
    return "\n".join(lines)


def _sha256(data):
    """Lowercase hex SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def _digest_text(digest):
    """Reject a digest that is not 64 lowercase hex characters."""
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise ValueError("digest must be 64 lowercase hex characters")


def _header_line(key, binary, digest=None, folds=None, geometry=GEOMETRY_LEGACY, passes=None):
    """The one-line envelope stored ahead of a folded payload.

    No digest selects version 1. A digest selects version 2. A digest
    and a fold sequence select version 3, which records the sequence.
    Multiscale geometry selects version 4 and records the pass count.
    """
    mode = "bin" if binary else "text"
    if geometry == GEOMETRY_MULTISCALE:
        if folds is not None:
            raise ValueError("multiscale geometry does not record a fold list")
        if digest is None:
            raise ValueError("multiscale geometry needs a digest")
        _check_passes(passes)
        _digest_text(digest)
        flag = "1" if key else "0"
        return (
            f"TESSERACT-FOLD/4 key={flag} mode={mode} sha256={digest} "
            f"geometry=multiscale passes={passes}\n"
        ).encode("ascii")
    if folds is not None:
        if digest is None:
            raise ValueError("a recorded fold sequence needs a digest")
        if key:
            raise ValueError("a recorded fold sequence does not take a key")
        _digest_text(digest)
        spec = fold_spec(folds)
        return (
            f"TESSERACT-FOLD/3 key=0 mode={mode} sha256={digest} folds={spec}\n"
        ).encode("ascii")
    flag = "1" if key else "0"
    if digest is None:
        return f"TESSERACT-FOLD/1 key={flag} mode={mode}\n".encode("ascii")
    _digest_text(digest)
    return (
        f"TESSERACT-FOLD/2 key={flag} mode={mode} sha256={digest}\n"
    ).encode("ascii")


def split_header(data):
    """Return (key_used, binary, digest, folds, geometry, passes, payload) or None.

    digest is a hex string, or None for a version 1 header. folds is a
    tuple of folds, or None when the header does not record a sequence.
    geometry is legacy for versions 1 to 3 and multiscale for version 4.
    passes is an int for version 4 and None otherwise. payload is bytes.
    Return None when the leading bytes are not a header. A line that
    starts like a header and does not parse is left for the caller to reject.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("header data must be bytes")
    match = HEADER_V4_RE.match(data)
    if match is not None:
        passes = int(match.group(4))
        if passes > MAX_PASSES:
            return None
        return (
            match.group(1) == b"1",
            match.group(2) == b"bin",
            match.group(3).decode("ascii"),
            None,
            GEOMETRY_MULTISCALE,
            passes,
            bytes(data[match.end():]),
        )
    match = HEADER_V3_RE.match(data)
    if match is not None:
        binary = match.group(1) == b"bin"
        digest = match.group(2).decode("ascii")
        try:
            folds = parse_folds(match.group(3).decode("ascii"))
        except ValueError:
            return None
        return (
            False,
            binary,
            digest,
            folds,
            GEOMETRY_LEGACY,
            None,
            bytes(data[match.end():]),
        )
    match = HEADER_V2_RE.match(data)
    if match is not None:
        key_used = match.group(1) == b"1"
        binary = match.group(2) == b"bin"
        digest = match.group(3).decode("ascii")
        return (
            key_used,
            binary,
            digest,
            None,
            GEOMETRY_LEGACY,
            None,
            bytes(data[match.end():]),
        )
    match = HEADER_V1_RE.match(data)
    if match is not None:
        key_used = match.group(1) == b"1"
        binary = match.group(2) == b"bin"
        return key_used, binary, None, None, GEOMETRY_LEGACY, None, bytes(data[match.end():])
    return None


def pack_document(
    payload,
    key,
    binary,
    header,
    digest=None,
    folds=None,
    geometry=GEOMETRY_LEGACY,
    passes=None,
):
    """Return bytes, with a header in front when `header` is true.

    A text payload is a str and is encoded as UTF-8. A binary payload
    is already bytes. `digest` is the SHA-256 hex of the original bytes.
    When folds are passed with a digest, the header is version 3 and
    records that sequence. Multiscale geometry with a digest is version 4
    and records `passes`. A digest alone is version 2. Neither is version 1.
    """
    if binary:
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("binary payload must be bytes")
        body = bytes(payload)
    else:
        if not isinstance(payload, str):
            raise TypeError("text payload must be a string")
        body = payload.encode("utf-8")
    if not header:
        return body
    return _header_line(key, binary, digest, folds, geometry, passes) + body


def check_digest(restored, binary, digest):
    """Raise ValueError when restored bytes do not match `digest`."""
    if binary:
        raw = bytes(restored)
    else:
        raw = restored.encode("utf-8")
    if _sha256(raw) != digest:
        raise ValueError(
            "restored data does not match the stored digest; "
            "the key, the fold sequence, or the pass count may be wrong, "
            "or the file is damaged"
        )


def unpack_document(data, key, binary, raw):
    """Return (payload, binary, digest, folds, geometry, passes).

    A recognized header chooses the mode and checks the key against the
    flag it stored. digest is None for version 1, for input with no
    header, and for `raw`. folds is the recorded sequence, or None.
    geometry is legacy, multiscale, or None when there is no header.
    passes is the recorded count, or None. `raw` skips the header and
    treats every byte as payload. A broken header line is an error.
    Text payload is returned as a str. Binary payload is bytes. The
    digest is not checked here; call check_digest after unfolding.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("document must be bytes")
    data = bytes(data)
    digest = None
    folds = None
    geometry = None
    passes = None
    if not raw and data.startswith(b"TESSERACT-FOLD-FOLDER/"):
        raise ValueError("this file is a folder package; restore the folder")
    if not raw and data.startswith(b"TESSERACT-FOLD/"):
        found = split_header(data)
        if found is None:
            raise ValueError("damaged header")
        key_used, header_binary, digest, folds, geometry, passes, payload = found
        if key_used and key == "":
            raise ValueError("this fold used a key; pass --key PHRASE")
        if not key_used and key != "":
            raise ValueError("this fold used no key; omit --key")
        binary = header_binary
        data = payload
    if binary:
        return data, True, digest, folds, geometry, passes
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "input is not UTF-8 text; decrypt raw bytes with --binary"
        ) from exc
    return text, False, digest, folds, geometry, passes


def tracked_coords(length, folds):
    """Return (start, after_each, end) coordinates for the filled vertices.

    start[i] is where symbol i was written. after_each[k][i] is where it
    sits after fold k. end is after_each[-1], or start when there are
    no folds.
    """
    side = side_for(length)
    start = [tuple(index_to_coord(index, side)) for index in range(length)]
    current = [list(coord) for coord in start]
    frames = []
    for fold in folds:
        for coord in current:
            apply_fold(coord, fold, side)
        frames.append([tuple(coord) for coord in current])
    end = frames[-1] if frames else start
    return start, frames, end


def _glyph(symbol):
    """One column for a map cell. Unusual characters become a mark."""
    if isinstance(symbol, int):
        if 32 <= symbol <= 126:
            symbol = chr(symbol)
        else:
            return "."
    if symbol == " ":
        return "\u2423"
    if symbol == "\n":
        return "\u21b5"
    if symbol == "\t":
        return "\u21e5"
    if len(symbol) != 1 or not symbol.isprintable():
        return "?"
    width = unicodedata.east_asian_width(symbol)
    if width in ("W", "F", "A"):
        return "?"
    return symbol


def format_grid(placed, side):
    """Draw filled vertices. `placed` maps (x, y, z, w) to a glyph.

    Side 2 is one tesseract and is drawn as the w = 0 cube and the
    w = 1 cube. Each cube is two squares, z = 0 and z = 1. x increases
    to the right and y increases downward. A larger side is drawn the
    same way only when it is still 2. Callers with a bigger grid use
    the coordinate table instead.
    """
    lines = []
    for w in range(side):
        lines.append(f"w={w}")
        for z in range(side):
            lines.append(f"  z={z}")
            for y in range(side):
                cells = []
                for x in range(side):
                    cells.append(placed.get((x, y, z, w), "."))
                lines.append(f"    y={y}  " + " ".join(cells))
    return "\n".join(lines)


def _place(symbols, coords):
    placed = {}
    for symbol, coord in zip(symbols, coords):
        placed[coord] = _glyph(symbol)
    return placed


def trace_indexes(length, requested):
    """Write indexes to follow. `requested` None uses a short sample."""
    if requested is not None:
        indexes = []
        for index in requested:
            if isinstance(index, bool) or not isinstance(index, int):
                raise TypeError("trace index must be an integer")
            if index < 0 or index >= length:
                raise ValueError(
                    f"trace index {index} is outside 0..{max(length - 1, 0)}"
                )
            indexes.append(index)
        return indexes
    if length <= 16:
        return list(range(length))
    chosen = []
    for index in (0, 1, 2, 3, length - 1):
        if 0 <= index < length and index not in chosen:
            chosen.append(index)
    return chosen


def format_paths(symbols, folds, indexes):
    """One line per symbol: its (x, y, z, w) after every fold."""
    if not symbols:
        return "  (no symbols)"
    side = side_for(len(symbols))
    binary = isinstance(symbols[0], int)
    lines = []
    for index in indexes:
        coord = index_to_coord(index, side)
        if binary:
            label = f"{symbols[index]:02x}"
        else:
            label = _glyph(symbols[index])
        points = [_fmt_coord(coord)]
        for fold in folds:
            apply_fold(coord, fold, side)
            points.append(_fmt_coord(coord))
        lines.append(f"  [{index}] {label}  " + " -> ".join(points))
    return "\n".join(lines)


def _fmt_coord(coord):
    return f"({coord[0]},{coord[1]},{coord[2]},{coord[3]})"


def _multiscale_paths(symbols, frames, indexes):
    """One line per symbol: its (x, y, z, w) after every multiscale pass."""
    if not symbols:
        return "  (no symbols)"
    side = side_for(len(symbols))
    binary = isinstance(symbols[0], int)
    lines = []
    for index in indexes:
        if binary:
            label = f"{symbols[index]:02x}"
        else:
            label = _glyph(symbols[index])
        points = [_fmt_coord(index_to_coord(index, side))]
        for frame in frames:
            points.append(_fmt_coord(frame[index]))
        lines.append(f"  [{index}] {label}  " + " -> ".join(points))
    return "\n".join(lines)


def _format_multiscale_map(items, key, passes, trace):
    """Trace multiscale passes. The grid is drawn only for one tesseract."""
    if isinstance(items, str):
        symbols = list(items)
        binary = False
    elif isinstance(items, (bytes, bytearray)):
        symbols = list(items)
        binary = True
    else:
        raise TypeError("data must be a string or bytes")
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    _check_passes(passes)
    frames, side = _multiscale_coords(len(symbols), key, passes)
    cells = side ** 4
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}, {cells} vertices"
    lines = [
        "TESSERACT FOLD MAP",
        f"{figure}; {len(symbols)} filled",
        "x increases to the right. y increases downward.",
        f"multiscale geometry, {_pass_count_text(passes)}",
        "Each pass folds the whole hypercube, then the blocks inside it,",
        "then the arrangement of those blocks, then the whole hypercube again.",
    ]
    if side == MIN_SIDE:
        start = [tuple(index_to_coord(index, side)) for index in range(len(symbols))]
        lines.append("")
        lines.append("Write order, before the folds:")
        lines.append(format_grid(_place(symbols, start), side))
        for number, frame in enumerate(frames, start=1):
            lines.append("")
            lines.append(f"After pass {number}:")
            lines.append(format_grid(_place(symbols, frame), side))
    lines.append("")
    lines.append("Symbol paths, (x, y, z, w) after each pass:")
    lines.append(_multiscale_paths(symbols, frames, trace_indexes(len(symbols), trace)))
    lines.append("")
    lines.append("Read in coordinate order:")
    reading = scramble_multiscale(items, key, passes)
    if binary:
        lines.append(reading.hex(" "))
    else:
        lines.append(reading)
    return "\n".join(lines)


def format_map(items, key="", folds=None, trace=None, geometry=GEOMETRY_LEGACY, passes=1):
    """Trace the folds of items. items is a str or bytes."""
    if geometry == GEOMETRY_MULTISCALE and folds is None:
        return _format_multiscale_map(items, key, passes, trace)
    if isinstance(items, str):
        symbols = list(items)
        binary = False
    elif isinstance(items, (bytes, bytearray)):
        symbols = list(items)
        binary = True
    else:
        raise TypeError("data must be a string or bytes")
    chosen = active_folds(key, folds)
    side = side_for(len(symbols))
    cells = side ** 4
    if side == MIN_SIDE:
        figure = "one tesseract, 16 vertices"
    else:
        figure = f"a hypercube of side {side}, {cells} vertices"
    lines = [
        "TESSERACT FOLD MAP",
        f"{figure}; {len(symbols)} filled",
        "x increases to the right. y increases downward.",
        describe_folds(chosen),
    ]
    if side == MIN_SIDE:
        start, frames, _end = tracked_coords(len(symbols), chosen)
        lines.append("")
        lines.append("Write order, before the folds:")
        lines.append(format_grid(_place(symbols, start), side))
        for number, (fold, frame) in enumerate(zip(chosen, frames), start=1):
            lines.append("")
            lines.append(f"After fold {number}: {describe_fold(fold)}")
            lines.append(format_grid(_place(symbols, frame), side))
    lines.append("")
    lines.append("Symbol paths, (x, y, z, w) after each fold:")
    lines.append(format_paths(symbols, chosen, trace_indexes(len(symbols), trace)))
    lines.append("")
    lines.append("Read in coordinate order:")
    reading = scramble(items, folds=chosen)
    if binary:
        lines.append(reading.hex(" "))
    else:
        lines.append(reading)
    return "\n".join(lines)


def check_folds():
    """Return a list of failures. An empty list means the geometry holds.

    Every catalog fold must be a bijection on side 2 and side 4. A hinge
    restores a vertex after four turns, and a mirror, crease, or half fold
    restores it after two. The canonical six folds must move the 16
    vertices of one tesseract onto 16 different vertices. Hello must fold
    to lloeH and fold back.
    """
    failures = []
    for side in (MIN_SIDE, 4):
        count = side ** 4
        for fold in CATALOG:
            images = []
            for index in range(count):
                coord = index_to_coord(index, side)
                apply_fold(coord, fold, side)
                images.append(coord_to_index(coord, side))
            if len(set(images)) != count:
                failures.append(f"{describe_fold(fold)} is not a bijection on side {side}")
        identity = list(range(count))
        for kind, times in (("hinge", 4), ("mirror", 2), ("diagonal", 2), ("half", 2)):
            for fold in CATALOG:
                if fold[0] != kind:
                    continue
                coords = [index_to_coord(index, side) for index in range(count)]
                for _ in range(times):
                    for coord in coords:
                        apply_fold(coord, fold, side)
                got = [coord_to_index(coord, side) for coord in coords]
                if got != identity:
                    failures.append(
                        f"{describe_fold(fold)} did not return after {times} on side {side}"
                    )
    canonical_images = []
    for index in range(16):
        coord = index_to_coord(index, MIN_SIDE)
        apply_folds(coord, CANONICAL, MIN_SIDE)
        canonical_images.append(coord_to_index(coord, MIN_SIDE))
    if len(set(canonical_images)) != 16:
        failures.append("canonical folds collide on one tesseract")
    if canonical_images == list(range(16)):
        failures.append("canonical folds left the tesseract unmoved")
    if scramble("Hello") != "lloeH":
        failures.append("Hello did not fold to lloeH")
    if restore(scramble("Hello")) != "Hello":
        failures.append("Hello did not unfold")
    hello_map = format_map("Hello", "")
    if not hello_map.endswith("Read in coordinate order:\nlloeH"):
        failures.append("map reading does not match the fold of Hello")
    longer = "abcdefghijklmnopq"
    if not format_map(longer, "").endswith(
        "Read in coordinate order:\n" + scramble(longer)
    ):
        failures.append("map reading does not match a side-4 fold")
    if restore(scramble(longer, "paper"), "paper") != longer:
        failures.append("keyed round trip failed")
    if parse_folds(CANONICAL_SPEC) != CANONICAL:
        failures.append("canonical names do not match the six folds")
    if fold_spec(CANONICAL) != CANONICAL_SPEC:
        failures.append("canonical folds do not record as their short names")
    mirror = parse_folds("mx,mx")
    _steps, final = analyze_sequence(5, mirror)
    if not final["identity"]:
        failures.append("two mirrors did not restore the arrangement")
    if len(_steps) != 2 or _steps[1]["change"] != "reversed":
        failures.append("the second mirror did not reverse the first")
    hello_dest = destination_ranks(5, CANONICAL)
    order, _lengths = permutation_order(hello_dest)
    if order < 2:
        failures.append("canonical folds have no repeated-fold order on Hello")
    if permute_power(hello_dest, order) != list(range(5)):
        failures.append("permutation order did not restore Hello's positions")
    tinkerer = fold_plan("Tim-the-tinkerer")
    if fold_spec(tinkerer) != "yw+,yz-,hy-,dyz,yw-,dyw":
        failures.append("Tim-the-tinkerer no longer selects the legacy plan")
    tinkerer_axes = set()
    for fold in tinkerer:
        tinkerer_axes.update(axes_of(fold))
    if 0 in tinkerer_axes:
        failures.append("legacy Tim-the-tinkerer touches x")
    mixed_axes = set()
    for fold in fold_plan_mixed("Tim-the-tinkerer", 0, "global-a"):
        mixed_axes.update(axes_of(fold))
    if mixed_axes != {0, 1, 2, 3}:
        failures.append("multiscale plan missed an axis")
    if fold_plan_mixed("Tim-the-tinkerer", 0, "global-a") == fold_plan_mixed(
        "Tim-the-tinkerer", 1, "global-a"
    ):
        failures.append("pass 0 and pass 1 derived the same folds")
    sample = "The quick brown fox jumps over the lazy dog."
    folded = scramble_multiscale(sample, "Tim-the-tinkerer", 2)
    if restore_multiscale(folded, "Tim-the-tinkerer", 2) != sample:
        failures.append("multiscale round trip failed")
    if scramble_multiscale("Hello") == "lloeH":
        failures.append("multiscale Hello matched the legacy fold")
    return failures


def sibling_path(path, decrypting):
    """Return the file written beside `path` when --output is omitted.

    Encrypting note.txt writes note.tess.txt. Decrypting note.tess.txt
    writes note.txt. Decrypting a name with no .tess marker writes
    note.plain.txt.
    """
    stem = path.stem
    suffix = path.suffix
    if decrypting and stem.endswith(".tess"):
        return path.with_name(stem[: -len(".tess")] + suffix)
    if decrypting and suffix == ".tess":
        return path.with_name(stem)
    if decrypting:
        return path.with_name(stem + ".plain" + suffix)
    return path.with_name(stem + ".tess" + suffix)


def _looks_like_path(word):
    """True when a word is a path rather than a plain message."""
    if "/" in word or word.startswith("~"):
        return True
    return Path(word).suffix != ""


def _positional_files(words):
    """Return the words when every one is an existing regular file."""
    paths = [Path(word).expanduser() for word in words]
    if paths and all(path.is_file() for path in paths):
        return paths
    return None


def _take_value(args, index, arg, flag):
    """Read the value for flag. `--flag=value` may start with a dash.

    A following word that starts with a dash is refused, so a missing
    value is not silently taken from the next option. `--file=-` is the
    exception and means standard input.
    """
    prefix = flag + "="
    if arg.startswith(prefix):
        value = arg[len(prefix):]
        if value == "":
            raise ValueError(f"{flag} needs a value")
        return value, index
    if index + 1 >= len(args):
        raise ValueError(f"{flag} needs a value")
    value = args[index + 1]
    if value.startswith("-") and not (flag == "--file" and value == "-"):
        raise ValueError(f"{flag} needs a value")
    return value, index + 1


def _parse_trace(text):
    """Return write indexes from `0,4,7`."""
    indexes = []
    for part in text.split(","):
        part = part.strip()
        if not part.isdigit():
            raise ValueError(f"--trace needs indexes, not {part or text}")
        indexes.append(int(part))
    if not indexes:
        raise ValueError("--trace needs an index")
    return indexes


def _parse_length(text):
    """Return a non-negative length, or raise ValueError."""
    if not text.isdigit():
        raise ValueError("--length needs a non-negative integer")
    return int(text)


def _parse_passes(text):
    """Return a pass count from 1 to MAX_PASSES, or raise ValueError."""
    if not text.isdigit():
        raise ValueError(f"--passes must be from 1 to {MAX_PASSES}")
    passes = int(text)
    if not 1 <= passes <= MAX_PASSES:
        raise ValueError(f"--passes must be from 1 to {MAX_PASSES}")
    return passes


def _parse_args(args):
    """Parse argv after the program name. Return a settings dict."""
    settings = {
        "decrypting": False,
        "key": "",
        "file_name": None,
        "output_name": None,
        "binary": False,
        "header": False,
        "raw": False,
        "show_map": False,
        "force_text": False,
        "menu": False,
        "check": False,
        "analyze": False,
        "repeat": False,
        "explore": False,
        "folds": None,
        "length": None,
        "compare": None,
        "compare_folds": None,
        "trace": None,
        "force": False,
        "legacy": False,
        "passes": None,
        "folder_name": None,
        "words": [],
        "saw_words": False,
        "key_set": False,
    }
    index = 0
    ended = False
    while index < len(args):
        arg = args[index]
        if ended:
            settings["words"].append(arg)
            settings["saw_words"] = True
            index += 1
            continue
        if arg == "--":
            ended = True
            index += 1
            continue
        if arg in ("-d", "--decrypt"):
            settings["decrypting"] = True
        elif arg in ("-m", "--map"):
            settings["show_map"] = True
        elif arg in ("-t", "--text"):
            settings["force_text"] = True
        elif arg == "--binary":
            settings["binary"] = True
        elif arg == "--header":
            settings["header"] = True
        elif arg == "--raw":
            settings["raw"] = True
        elif arg == "--force":
            settings["force"] = True
        elif arg == "--legacy":
            settings["legacy"] = True
        elif arg == "--passes" or arg.startswith("--passes="):
            value, index = _take_value(args, index, arg, "--passes")
            if settings["passes"] is not None:
                raise ValueError("--passes can be used once")
            settings["passes"] = _parse_passes(value)
        elif arg == "--menu":
            settings["menu"] = True
        elif arg == "--check":
            settings["check"] = True
        elif arg in ("--analyze", "--analysis"):
            settings["analyze"] = True
        elif arg == "--repeat":
            settings["repeat"] = True
        elif arg == "--explore":
            settings["explore"] = True
        elif arg in ("-k", "--key") or arg.startswith("--key="):
            value, index = _take_value(args, index, arg, "--key")
            settings["key"] = value
            settings["key_set"] = True
        elif arg == "--folds" or arg.startswith("--folds="):
            value, index = _take_value(args, index, arg, "--folds")
            if settings["folds"] is not None:
                raise ValueError("--folds can be used once")
            settings["folds"] = parse_folds(value)
        elif arg == "--compare" or (
            arg.startswith("--compare=") and not arg.startswith("--compare-folds")
        ):
            if arg == "--compare=":
                value = ""
            else:
                value, index = _take_value(args, index, arg, "--compare")
            if settings["compare"] is not None:
                raise ValueError("--compare can be used once")
            settings["compare"] = value
        elif arg == "--compare-folds" or arg.startswith("--compare-folds="):
            value, index = _take_value(args, index, arg, "--compare-folds")
            if settings["compare_folds"] is not None:
                raise ValueError("--compare-folds can be used once")
            settings["compare_folds"] = parse_folds(value)
        elif arg == "--length" or arg.startswith("--length="):
            value, index = _take_value(args, index, arg, "--length")
            if settings["length"] is not None:
                raise ValueError("--length can be used once")
            settings["length"] = _parse_length(value)
        elif arg == "--trace" or arg.startswith("--trace="):
            value, index = _take_value(args, index, arg, "--trace")
            if settings["trace"] is not None:
                raise ValueError("--trace can be used once")
            settings["trace"] = _parse_trace(value)
        elif arg in ("-f", "--file") or arg.startswith("--file="):
            value, index = _take_value(args, index, arg, "--file")
            if settings["file_name"] is not None:
                raise ValueError("--file can be used once")
            settings["file_name"] = value
        elif arg == "--folder" or arg.startswith("--folder="):
            value, index = _take_value(args, index, arg, "--folder")
            if settings["folder_name"] is not None:
                raise ValueError("--folder can be used once")
            settings["folder_name"] = value
        elif arg in ("-o", "--output") or arg.startswith("--output="):
            value, index = _take_value(args, index, arg, "--output")
            if settings["output_name"] is not None:
                raise ValueError("--output can be used once")
            settings["output_name"] = value
        elif arg.startswith("-"):
            raise ValueError(f"unknown argument {arg}")
        else:
            settings["words"].append(arg)
            settings["saw_words"] = True
        index += 1
    _check_settings(settings)
    return settings


def _reject_folder_mode_flags(settings):
    """Folder packing is one archive. It does not take the text-mode flags."""
    names = []
    if settings["show_map"]:
        names.append("--map")
    if settings["analyze"]:
        names.append("--analyze")
    if settings["repeat"]:
        names.append("--repeat")
    if settings["explore"]:
        names.append("--explore")
    if settings["raw"]:
        names.append("--raw")
    if settings["header"]:
        names.append("--header")
    if settings["binary"]:
        names.append("--binary")
    if settings["force_text"]:
        names.append("--text")
    if settings["trace"] is not None:
        names.append("--trace")
    if settings["length"] is not None:
        names.append("--length")
    if settings["compare"] is not None:
        names.append("--compare")
    if settings["compare_folds"] is not None:
        names.append("--compare-folds")
    if names:
        raise ValueError(
            "folder mode cannot be combined with " + " or ".join(names)
        )


def _check_settings(settings):
    """Reject flag combinations that do not describe one operation."""
    if settings["header"] and settings["raw"]:
        raise ValueError("--header and --raw cannot be combined")
    if settings["force"] and settings["output_name"] is None:
        raise ValueError("--force needs --output")
    if settings["binary"] and settings["force_text"]:
        raise ValueError("--binary and --text cannot be combined")
    if settings["folds"] is not None and settings["key_set"]:
        raise ValueError("pass --key or --folds, not both")
    if settings["legacy"] and settings["passes"] is not None:
        raise ValueError("--passes and --legacy cannot be combined")
    if settings["folds"] is not None and settings["passes"] is not None:
        raise ValueError("--passes and --folds cannot be combined")
    if settings["compare_folds"] is not None and settings["passes"] is not None:
        raise ValueError("--passes and --compare-folds cannot be combined")
    if settings["compare"] is not None and settings["compare_folds"] is not None:
        raise ValueError("pass --compare or --compare-folds, not both")
    if settings["compare"] is not None and not settings["explore"]:
        raise ValueError("--compare needs --explore")
    if settings["compare_folds"] is not None and not settings["explore"]:
        raise ValueError("--compare-folds needs --explore")
    if settings["length"] is not None and not (
        settings["explore"] or settings["repeat"]
    ):
        raise ValueError("--length needs --explore or --repeat")
    if settings["trace"] is not None:
        settings["show_map"] = True
    modes = [
        name
        for name in ("check", "menu", "explore", "repeat")
        if settings[name]
    ]
    if len(modes) > 1:
        raise ValueError("--" + " and --".join(modes) + " cannot be combined")
    quiet = (
        settings["decrypting"]
        or settings["show_map"]
        or settings["analyze"]
        or settings["binary"]
        or settings["header"]
        or settings["raw"]
        or settings["force_text"]
        or settings["key_set"]
        or settings["folds"] is not None
        or settings["file_name"] is not None
        or settings["output_name"] is not None
        or settings["saw_words"]
        or settings["length"] is not None
        or settings["compare"] is not None
        or settings["compare_folds"] is not None
        or settings["trace"] is not None
        or settings["force"]
        or settings["legacy"]
        or settings["passes"] is not None
        or settings["folder_name"] is not None
    )
    if settings["check"] and quiet:
        raise ValueError("--check does not take other arguments")
    if settings["menu"] and quiet:
        raise ValueError("--menu does not take other arguments")
    if settings["explore"] and (
        settings["decrypting"]
        or settings["show_map"]
        or settings["analyze"]
        or settings["binary"]
        or settings["header"]
        or settings["raw"]
        or settings["force_text"]
        or settings["output_name"] is not None
        or settings["file_name"] is not None
    ):
        raise ValueError("--explore only takes a length, a key, and folds")
    if settings["repeat"] and settings["output_name"] is not None:
        raise ValueError("--repeat does not write a file")
    if settings["repeat"] and (
        settings["decrypting"] or settings["analyze"] or settings["show_map"]
    ):
        raise ValueError("--repeat cannot be combined with that option")
    if settings["folder_name"] is not None:
        _reject_folder_mode_flags(settings)


def _read_stdin_bytes():
    return sys.stdin.buffer.read()


def _write_stdout_text(text, add_newline):
    try:
        sys.stdout.write(text)
        if add_newline:
            sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        return 0
    except UnicodeEncodeError:
        print(f"{NAME}: the result cannot be encoded for this terminal", file=sys.stderr)
        return 1
    return 0


def _write_stdout_bytes(data):
    try:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        return 0
    return 0


def _emit_map(items, key, folds=None, trace=None, geometry=GEOMETRY_LEGACY, passes=1):
    if passes is None:
        passes = 1
    print(format_map(items, key, folds, trace, geometry, passes), file=sys.stderr)


def _emit_analysis(items, key, folds=None, geometry=GEOMETRY_LEGACY, passes=1):
    if passes is None:
        passes = 1
    print(format_analysis(items, key, folds, geometry, passes), file=sys.stderr)


def _write_file(path, data):
    """Write bytes to path by replacing a finished temporary file.

    The temporary file is in the destination folder, so the replace stays
    on one filesystem. A failure removes the temporary file and leaves an
    existing destination unchanged.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix="." + path.name + ".",
        suffix=".partial",
        dir=path.parent,
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def _confirm_replace(path, force):
    """Replace an existing --output file only with consent or --force.

    At a terminal, ask. Anywhere else, refuse unless `force` is true.
    --force replaces without asking. An empty answer, or any answer
    other than y or yes, leaves the file.
    """
    if not path.exists():
        return
    if force:
        return
    if sys.stdin.isatty() and sys.stdout.isatty():
        # Print the question ourselves. input() sends its prompt to stdout
        # unless both streams are real terminal files, and this program's
        # other notices already go to stderr.
        prompt = f"{NAME}: {path} already exists. Replace it? [y/N] "
        print(prompt, file=sys.stderr, end="", flush=True)
        try:
            reply = input()
        except EOFError:
            reply = ""
        if reply.strip().lower() not in ("y", "yes"):
            raise OSError(f"left {path} unchanged")
        return
    raise OSError(f"{path} already exists; pass --force to replace it")


def _select_geometry(settings, header_geometry, header_passes):
    """Return (geometry, passes) for one document.

    A header wins. passes is None for legacy geometry. header_geometry
    is None when the input has no header. A requested pass count that
    disagrees with the header is an error, before anything is written.
    """
    requested = settings.get("passes")
    legacy_flag = settings.get("legacy", False)
    folds = settings.get("folds")
    if header_geometry == GEOMETRY_MULTISCALE:
        if legacy_flag:
            raise ValueError("this file uses multiscale geometry; omit --legacy")
        if folds is not None:
            raise ValueError("this file uses multiscale geometry; omit --folds")
        if requested is not None and requested != header_passes:
            raise ValueError(
                f"this file records {header_passes} passes; "
                f"omit --passes or pass {header_passes}"
            )
        return GEOMETRY_MULTISCALE, header_passes
    if header_geometry == GEOMETRY_LEGACY:
        if requested is not None:
            raise ValueError("this file uses legacy geometry; omit --passes")
        return GEOMETRY_LEGACY, None
    if folds is not None or legacy_flag:
        return GEOMETRY_LEGACY, None
    if requested is None:
        requested = 1
    return GEOMETRY_MULTISCALE, requested


def _transform_bytes(data, settings, from_file):
    """Fold or unfold one document.

    Return (output bytes, map subject, binary, folds, geometry, passes).
    The map subject is the plaintext string or bytes the map should
    trace. binary is true when the output bytes are a raw payload rather
    than UTF-8 text. folds is the legacy sequence that was applied,
    including one read from a version 3 header. geometry is legacy or
    multiscale. passes is the multiscale count, or None for legacy.
    A digest is checked after unfolding and before anything is written.
    """
    key = settings["key"]
    folds = settings.get("folds")
    binary = settings["binary"]
    if settings["decrypting"]:
        payload, binary, digest, header_folds, header_geometry, header_passes = unpack_document(
            data, key, binary, settings["raw"]
        )
        geometry, passes = _select_geometry(settings, header_geometry, header_passes)
        if geometry == GEOMETRY_LEGACY:
            if header_folds is not None:
                if folds is not None and tuple(folds) != header_folds:
                    raise ValueError(
                        "this file records folds "
                        + fold_spec(header_folds)
                        + "; omit --folds or pass that sequence"
                    )
                folds = header_folds
            restored = restore(payload, key, folds)
        else:
            folds = None
            restored = restore_multiscale(payload, key, passes)
        if digest is not None:
            check_digest(restored, binary, digest)
        out = pack_document(restored, key, binary, False)
        return out, restored, binary, folds, geometry, passes
    geometry, passes = _select_geometry(settings, None, None)
    if binary:
        plain = data
        digest_bytes = bytes(data)
    else:
        try:
            plain = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "input is not UTF-8 text; scramble raw bytes with --binary"
            ) from exc
        digest_bytes = plain.encode("utf-8")
    if geometry == GEOMETRY_MULTISCALE:
        folded = scramble_multiscale(plain, key, passes)
        folds = None
    else:
        folded = scramble(plain, key, folds)
    use_header = settings["header"] or (from_file and not settings["raw"])
    digest = _sha256(digest_bytes) if use_header else None
    if geometry == GEOMETRY_MULTISCALE:
        out = pack_document(
            folded,
            key,
            binary,
            use_header,
            digest,
            geometry=GEOMETRY_MULTISCALE,
            passes=passes,
        )
    else:
        recorded = folds if use_header and folds is not None else None
        out = pack_document(folded, key, binary, use_header, digest, recorded)
    return out, plain, binary, folds, geometry, passes


def _refuse_same_file(source, destination):
    try:
        if source.resolve() == destination.resolve() and destination.exists():
            raise OSError(f"refusing to replace the input file {source}")
    except OSError:
        raise
    if source == destination and destination.exists():
        raise OSError(f"refusing to replace the input file {source}")


def _transform_files(files, settings):
    """Fold each file onto its sibling path, or onto --output for one file."""
    jobs = []
    output_name = settings["output_name"]
    for path in files:
        source = path.expanduser()
        if not source.is_file():
            raise OSError(f"{source} is not a file")
        data = source.read_bytes()
        out, subject, _binary, used, geometry, passes = _transform_bytes(data, settings, True)
        if output_name is not None:
            destination = Path(output_name).expanduser()
            replace = True
        else:
            destination = sibling_path(source, settings["decrypting"])
            replace = False
            if destination.exists():
                raise OSError(
                    f"{destination} already exists; pass --output to replace it"
                )
        _refuse_same_file(source, destination)
        jobs.append((destination, out, subject, replace, used, geometry, passes))
    for destination, out, subject, replace, used, geometry, passes in jobs:
        if replace:
            _confirm_replace(destination, settings["force"])
        _write_file(destination, out)
        print(f"{NAME}: wrote {destination}", file=sys.stderr)
        if settings["show_map"]:
            _emit_map(subject, settings["key"], used, settings.get("trace"), geometry, passes)
        if settings.get("analyze"):
            _emit_analysis(subject, settings["key"], used, geometry, passes)
    return 0


def _validate_filename(name):
    """Refuse an empty, relative, or non-portable path component."""
    if (
        not name
        or name in (".", "..")
        or "/" in name
        or "\\" in name
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in name)
    ):
        raise ValueError(f"invalid file name: {name!r}")
    if len(name.encode("utf-8")) > _NAME_MAX_BYTES:
        raise ValueError("file name exceeds 255 UTF-8 bytes")
    return name


def _is_folder_package(path):
    """True when the file begins with a folder-package header."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        return False
    with path.open("rb") as handle:
        prefix = handle.read(len(b"TESSERACT-FOLD-FOLDER/"))
    return prefix == b"TESSERACT-FOLD-FOLDER/"


def _folder_members(folder):
    """Collect the tree. The root and empty directories are included.

    Symbolic links and special files are refused before anything is packed.
    """
    if folder.is_symlink() or not folder.is_dir():
        raise OSError("input folder must be a real directory, not a symlink")
    try:
        root_name = _validate_filename(folder.name)
    except ValueError as exc:
        raise ValueError("invalid folder name") from exc
    entries = []

    def visit(current, relative):
        entries.append((current, relative + "/", True))
        children = sorted(current.iterdir(), key=lambda item: item.name)
        for child in children:
            _validate_filename(child.name)
            if child.is_symlink():
                raise ValueError(f"symbolic links are not supported: {child}")
            member = relative + "/" + child.name
            if child.is_dir():
                visit(child, member)
            elif child.is_file():
                entries.append((child, member, False))
            else:
                raise ValueError(f"unsupported special file: {child}")

    visit(folder, root_name)
    return entries


def _write_folder_zip(destination, members):
    """Write a stored zip. Compression is not part of this program."""
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
    ) as archive:
        for path, member, _is_dir in members:
            archive.write(path, arcname=member)


def _folder_header_line(key, geometry, passes, digest, nbytes, folds):
    """One ASCII line. The key phrase is not stored."""
    flag = "1" if key else "0"
    _digest_text(digest)
    if geometry == GEOMETRY_MULTISCALE:
        if folds is not None:
            raise ValueError("multiscale geometry does not record a fold list")
        _check_passes(passes)
        line = (
            f"TESSERACT-FOLD-FOLDER/1 key={flag} geometry=multiscale "
            f"passes={passes} sha256={digest} bytes={nbytes}\n"
        )
    else:
        line = (
            f"TESSERACT-FOLD-FOLDER/1 key={flag} geometry=legacy "
            f"sha256={digest} bytes={nbytes}"
        )
        if folds is not None:
            if key:
                raise ValueError("a recorded fold sequence does not take a key")
            line += " folds=" + fold_spec(folds)
        line += "\n"
    return line.encode("ascii")


def _parse_folder_header(data):
    """Return key flag, geometry, passes, digest, length, folds, and payload.

    A line that starts like a folder header and does not parse is damaged.
    passes is an int for multiscale and None for legacy.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("folder package must be bytes")
    data = bytes(data)
    if not data.startswith(b"TESSERACT-FOLD-FOLDER/"):
        raise ValueError("this file is not a folder package")
    match = FOLDER_HEADER_RE.match(data)
    if match is None:
        raise ValueError("damaged folder header")
    key_used = match.group(1) == b"1"
    geometry = match.group(2).decode("ascii")
    passes_text = match.group(3)
    digest = match.group(4).decode("ascii")
    nbytes = int(match.group(5))
    folds_text = match.group(6)
    passes = int(passes_text) if passes_text is not None else None
    folds = None
    if geometry == GEOMETRY_MULTISCALE:
        if passes is None or passes > MAX_PASSES or folds_text is not None:
            raise ValueError("damaged folder header")
    elif geometry == GEOMETRY_LEGACY:
        if passes is not None or (folds_text is not None and key_used):
            raise ValueError("damaged folder header")
        if folds_text is not None:
            try:
                folds = parse_folds(folds_text.decode("ascii"))
            except ValueError:
                raise ValueError("damaged folder header") from None
    else:
        raise ValueError("damaged folder header")
    payload = data[match.end():]
    return key_used, geometry, passes, digest, nbytes, folds, payload


def _package_must_be_outside(source, destination):
    """The package would otherwise be packed into itself."""
    source_real = source.resolve()
    dest_real = destination.resolve()
    if dest_real == source_real or source_real in dest_real.parents:
        raise ValueError("the package must be outside the input folder")


def _refuse_package_target(destination):
    """A package replaces a file. It never replaces a directory or a link."""
    if destination.is_symlink() or destination.is_dir():
        if destination.is_dir():
            raise OSError(f"refusing to replace the directory {destination}")
        raise OSError(f"refusing to replace {destination}")


def _check_folder_destination_free(destination):
    """An existing tree is left alone, including when --force is set."""
    if destination.exists() or destination.is_symlink():
        raise OSError(
            f"{destination} already exists; pass --output to name a new folder"
        )


def _safe_folder_zip_members(archive, zip_length):
    """Permit one stored root directory and the files under it.

    Declared sizes are checked against the zip length before any byte is
    extracted, so a lying header cannot ask for a huge file.
    """
    try:
        members = archive.infolist()
    except zipfile.BadZipFile as exc:
        raise ValueError("damaged folder archive") from exc
    if not members:
        raise ValueError("folder archive is empty")
    roots = set()
    found = set()
    file_entries = set()
    folder_entries = set()
    total = 0
    for info in members:
        raw = info.filename
        if info.flag_bits & 0x1:
            raise ValueError("archive contains an encrypted member")
        if (
            info.file_size < 0
            or info.file_size > zip_length
            or info.compress_size > zip_length
        ):
            raise ValueError("archive member is larger than the zip")
        total += info.file_size
        if total > zip_length:
            raise ValueError("archive members are larger than the zip")
        if info.compress_type != zipfile.ZIP_STORED or info.compress_size != info.file_size:
            raise ValueError("folder archive must be stored, not compressed")
        if not raw or raw.startswith("/") or "\\" in raw or "\x00" in raw:
            raise ValueError("unsafe path in folder archive")
        components = raw.rstrip("/").split("/")
        if len(components) < 1 or any(not component for component in components):
            raise ValueError("invalid empty directory component in archive")
        for component in components:
            if component in (".", ".."):
                raise ValueError("unsafe path in folder archive")
            _validate_filename(component)
        name = "/".join(components)
        if name in found:
            raise ValueError("duplicate path in folder archive")
        found.add(name)
        roots.add(components[0])
        if len(roots) > 1:
            raise ValueError("folder archive contains multiple root directories")
        mode = info.external_attr >> 16
        if stat.S_IFMT(mode) == stat.S_IFLNK:
            raise ValueError("archive contains a symbolic link")
        if info.is_dir():
            if stat.S_IFMT(mode) not in (0, stat.S_IFDIR):
                raise ValueError("invalid directory entry type")
            folder_entries.add(name)
        else:
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError("unsupported archive member type")
            file_entries.add(name)
    root = next(iter(roots))
    if root not in folder_entries:
        raise ValueError("folder archive must contain a root directory")
    for name in found:
        parts = name.split("/")
        for index in range(1, len(parts)):
            if "/".join(parts[:index]) in file_entries:
                raise ValueError("file used as parent directory in archive")
    return root, members


def _restore_folder_zip(archive, members, stage):
    """Extract under stage, dropping the single archive root.

    Files are created exclusively. The caller's destination is not touched.
    """
    stage.mkdir()
    stage_real = stage.resolve()
    for info in members:
        pieces = info.filename.rstrip("/").split("/")
        relative = pieces[1:]
        if not relative:
            continue
        target = stage.joinpath(*relative)
        if stage_real not in target.resolve().parents:
            raise ValueError("unsafe path in folder archive")
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as src, target.open("xb") as out:
                shutil.copyfileobj(src, out, 1024 * 1024)


def _fold_archive(data, key, geometry, passes, folds, decrypting):
    """Fold or unfold the stored zip. The length does not change."""
    if geometry == GEOMETRY_MULTISCALE:
        if decrypting:
            return restore_multiscale(data, key, passes)
        return scramble_multiscale(data, key, passes)
    if decrypting:
        return restore(data, key, folds)
    return scramble(data, key, folds)


def encode_folder(source, settings):
    """Pack a folder as a stored zip and fold those bytes.

    Nothing in the source tree is modified. The default package is
    FolderName.tess beside the folder. Return the package path.
    """
    source = Path(source).expanduser()
    if source.is_symlink():
        raise OSError("input folder must be a real directory, not a symlink")
    if not source.is_dir():
        raise OSError(f"{source} is not a folder")
    members = _folder_members(source)
    output_name = settings.get("output_name")
    if output_name:
        destination = Path(output_name).expanduser()
        _refuse_package_target(destination)
        _confirm_replace(destination, settings.get("force", False))
    else:
        destination = source.with_name(source.name + ".tess")
        if destination.exists() or destination.is_symlink():
            raise OSError(
                f"{destination} already exists; pass --output to replace it"
            )
    _package_must_be_outside(source, destination)
    geometry, passes = _select_geometry(settings, None, None)
    key = settings["key"]
    folds = settings.get("folds")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".tesseract-folder-", dir=destination.parent
    ) as temp:
        archive_path = Path(temp) / "source.zip"
        _write_folder_zip(archive_path, members)
        raw = archive_path.read_bytes()
        digest = _sha256(raw)
        folded = _fold_archive(raw, key, geometry, passes, folds, False)
        recorded = folds if geometry == GEOMETRY_LEGACY else None
        header = _folder_header_line(
            key, geometry, passes, digest, len(raw), recorded
        )
        _write_file(destination, header + folded)
    return destination


def decode_folder(source, settings):
    """Restore a folder package. An existing folder is never replaced.

    The header selects the geometry and the pass count. --force does not
    delete a tree. Return the restored folder.
    """
    source = Path(source).expanduser()
    if source.is_symlink() or not source.is_file():
        raise OSError(f"{source} is not a folder package")
    data = source.read_bytes()
    (
        key_used,
        header_geometry,
        header_passes,
        digest,
        nbytes,
        header_folds,
        payload,
    ) = _parse_folder_header(data)
    key = settings["key"]
    if key_used and key == "":
        raise ValueError("this fold used a key; pass --key PHRASE")
    if not key_used and key != "":
        raise ValueError("this fold used no key; omit --key")
    geometry, passes = _select_geometry(settings, header_geometry, header_passes)
    folds = settings.get("folds")
    if geometry == GEOMETRY_LEGACY and header_folds is not None:
        if folds is not None and tuple(folds) != header_folds:
            raise ValueError(
                "this file records folds "
                + fold_spec(header_folds)
                + "; omit --folds or pass that sequence"
            )
        folds = header_folds
    if len(payload) != nbytes:
        raise ValueError("folder payload length does not match the header")
    restored = _fold_archive(payload, key, geometry, passes, folds, True)
    if len(restored) != nbytes or _sha256(restored) != digest:
        raise ValueError(
            "restored data does not match the stored digest; "
            "the key, the fold sequence, or the pass count may be wrong, "
            "or the file is damaged"
        )
    output_name = settings.get("output_name")
    parent = (
        Path(output_name).expanduser().parent
        if output_name
        else source.parent
    )
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".tesseract-folder-", dir=parent) as temp:
        archive_path = Path(temp) / "restored.zip"
        archive_path.write_bytes(restored)
        try:
            archive = zipfile.ZipFile(archive_path, "r")
        except zipfile.BadZipFile as exc:
            raise ValueError("damaged folder archive") from exc
        with archive:
            root, members = _safe_folder_zip_members(archive, len(restored))
            if output_name:
                destination = Path(output_name).expanduser()
            else:
                destination = source.parent / root
            _check_folder_destination_free(destination)
            staged = Path(temp) / "tree"
            try:
                _restore_folder_zip(archive, members, staged)
            except zipfile.BadZipFile as exc:
                raise ValueError("damaged folder archive") from exc
        _check_folder_destination_free(destination)
        staged.rename(destination)
    return destination


def _run_check():
    failures = check_folds()
    if failures:
        for failure in failures:
            print(f"{NAME}: {failure}", file=sys.stderr)
        return 1
    print(f"{NAME}: folds on side 2 and side 4 are bijections", file=sys.stderr)
    print(f"{NAME}: Hello -> {scramble('Hello')}", file=sys.stderr)
    print(f"{NAME}: check ok", file=sys.stderr)
    return 0


def _run_explore(settings):
    """Print a permutation report. The default length is one tesseract."""
    words = settings["words"]
    text = " ".join(words) if words else None
    length = settings["length"]
    if text is not None and length is not None and length != len(text):
        raise ValueError("--length does not match the text")
    if text is not None and length is None:
        length = len(text)
    if length is None:
        length = 16
    use_legacy = (
        settings["legacy"]
        or settings["folds"] is not None
        or settings["compare_folds"] is not None
    )
    passes = 1 if settings["passes"] is None else settings["passes"]
    if use_legacy:
        folds = active_folds(settings["key"], settings["folds"])
        other = None
        label = "the other sequence"
        if settings["compare_folds"] is not None:
            other = settings["compare_folds"]
            label = "the other fold sequence"
        elif settings["compare"] is not None:
            other = fold_plan(settings["compare"])
            if settings["compare"] == "":
                label = "the canonical folds"
            else:
                label = "the other key"
        report = format_explore(length, folds, other, label)
    else:
        other_key = None
        label = "the other key"
        if settings["compare"] is not None:
            other_key = settings["compare"]
            if settings["compare"] == "":
                label = "the unkeyed folds"
        report = format_multiscale_explore(
            length, settings["key"], passes, other_key, label
        )
    return _write_stdout_text(report, True)


def _repeat_specimen(settings, files, data):
    """Return the text, bytes, or length a repeated-fold run studies."""
    if settings["length"] is not None and files is not None:
        raise ValueError("--length cannot be combined with a file")
    if files is not None:
        if len(files) != 1:
            raise ValueError("--repeat needs one file")
        source = files[0].expanduser()
        if not source.is_file():
            raise OSError(f"{source} is not a file")
        raw = source.read_bytes()
        if settings["binary"]:
            return raw
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "input is not UTF-8 text; repeat raw bytes with --binary"
            ) from exc
    if settings["length"] is not None and not settings["saw_words"]:
        return settings["length"]
    if settings["binary"]:
        specimen = data
    else:
        try:
            specimen = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "input is not UTF-8 text; repeat raw bytes with --binary"
            ) from exc
    if settings["length"] is not None and settings["length"] != len(specimen):
        raise ValueError("--length does not match the text")
    return specimen


def _main(argv):
    args = argv[1:]
    for arg in args:
        if arg == "--":
            break
        if arg in ("-h", "--help"):
            print(__doc__.strip())
            return 0
    try:
        settings = _parse_args(args)
    except ValueError as exc:
        print(f"{NAME}: {exc}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    if settings["check"]:
        return _run_check()
    if settings["menu"] or (not args and sys.stdin.isatty() and sys.stdout.isatty()):
        return numbered_menu()
    if settings["explore"]:
        try:
            return _run_explore(settings)
        except ValueError as exc:
            print(f"{NAME}: {exc}", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2

    file_name = settings["file_name"]
    words = settings["words"]
    folder_kind = None
    try:
        if settings["folder_name"] is not None:
            if settings["saw_words"] or file_name is not None:
                raise ValueError("pass --folder or a message, not both")
            files = None
            data = b""
            from_file = True
        elif file_name is not None:
            if settings["saw_words"]:
                raise ValueError("pass text or --file, not both")
            if file_name == "-":
                data = _read_stdin_bytes()
                from_file = False
                files = None
            else:
                path = Path(file_name)
                expanded = path.expanduser()
                if expanded.is_dir():
                    if settings["decrypting"]:
                        raise OSError(f"{file_name} is not a folder package")
                    _reject_folder_mode_flags(settings)
                    folder_kind = "encode"
                files = [path]
                data = b""
                from_file = True
        elif not settings["saw_words"]:
            if settings["repeat"] and settings["length"] is not None:
                data = b""
                from_file = False
                files = None
            elif sys.stdin.isatty():
                if settings["repeat"]:
                    raise ValueError("pass text, a file, or --length")
                raise ValueError("pass text, a file, or --menu")
            else:
                data = _read_stdin_bytes()
            from_file = False
            files = None
        elif settings["force_text"]:
            text = " ".join(words)
            data = text.encode("utf-8")
            from_file = False
            files = None
        else:
            candidate = Path(words[0]).expanduser() if len(words) == 1 else None
            if candidate is not None and candidate.is_dir():
                if settings["decrypting"]:
                    raise OSError(f"{words[0]} is not a folder package")
                _reject_folder_mode_flags(settings)
                files = [Path(words[0])]
                data = b""
                from_file = True
                folder_kind = "encode"
            else:
                files = _positional_files(words)
            if folder_kind != "encode" and files is None:
                text = " ".join(words)
                data = text.encode("utf-8")
                from_file = False
                if len(words) == 1 and _looks_like_path(words[0]):
                    print(
                        f"{NAME}: {words[0]} is not a file, so the name was used as text",
                        file=sys.stderr,
                    )
            else:
                data = b""
                from_file = True
        if (
            folder_kind is None
            and files is not None
            and len(files) == 1
            and settings["decrypting"]
            and not settings["raw"]
            and _is_folder_package(files[0])
        ):
            _reject_folder_mode_flags(settings)
            folder_kind = "decode"
        if files is not None and settings["output_name"] is not None and len(files) != 1:
            raise ValueError("--output needs a single file")
    except ValueError as exc:
        print(f"{NAME}: {exc}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"{NAME}: {exc}", file=sys.stderr)
        return 1

    try:
        if settings["folder_name"] is not None:
            source = Path(settings["folder_name"])
            if settings["decrypting"]:
                destination = decode_folder(source, settings)
                print(f"{NAME}: restored {destination}", file=sys.stderr)
            else:
                destination = encode_folder(source, settings)
                print(f"{NAME}: wrote {destination}", file=sys.stderr)
            return 0
        if folder_kind == "encode":
            destination = encode_folder(files[0], settings)
            print(f"{NAME}: wrote {destination}", file=sys.stderr)
            return 0
        if folder_kind == "decode":
            destination = decode_folder(files[0], settings)
            print(f"{NAME}: restored {destination}", file=sys.stderr)
            return 0
        if settings["repeat"]:
            specimen = _repeat_specimen(settings, files, data)
            if settings["legacy"] or settings["folds"] is not None:
                report = format_repeat(specimen, settings["key"], settings["folds"])
            else:
                report = format_repeat(
                    specimen,
                    settings["key"],
                    geometry=GEOMETRY_MULTISCALE,
                    passes=1 if settings["passes"] is None else settings["passes"],
                )
            return _write_stdout_text(report, True)
        if files is not None:
            return _transform_files(files, settings)
        out, subject, binary, used, geometry, passes = _transform_bytes(
            data, settings, from_file
        )
        if settings["show_map"]:
            _emit_map(subject, settings["key"], used, settings["trace"], geometry, passes)
        if settings["analyze"]:
            _emit_analysis(subject, settings["key"], used, geometry, passes)
        if settings["output_name"] is not None:
            destination = Path(settings["output_name"]).expanduser()
            _confirm_replace(destination, settings["force"])
            _write_file(destination, out)
            print(f"{NAME}: wrote {destination}", file=sys.stderr)
            return 0
        # A header is raw bytes even when the payload was text.
        # Decrypt keeps the mode the header recorded.
        if binary or (settings["header"] and not settings["decrypting"]):
            return _write_stdout_bytes(out)
        text = out.decode("utf-8")
        add_newline = settings["saw_words"]
        return _write_stdout_text(text, add_newline)
    except ValueError as exc:
        print(f"{NAME}: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"{NAME}: {exc}", file=sys.stderr)
        return 1


class _MenuBack(Exception):
    """Return to the numbered menu."""


def _ask(prompt):
    """Read one line. `:back` leaves the current operation."""
    try:
        reply = input(prompt)
    except EOFError:
        print(file=sys.stderr)
        raise _MenuExit
    except KeyboardInterrupt:
        print(file=sys.stderr)
        raise _MenuBack
    if reply.strip().lower() == ":back":
        raise _MenuBack
    return reply


class _MenuExit(Exception):
    """Standard input ended."""


def _ask_key():
    reply = _ask("Key phrase (Enter for none): ")
    return reply


def _menu_geometry():
    """Return (legacy, passes), or None when the answer cannot be used.

    An empty answer leaves the pass count unset. Folding then uses one
    multiscale pass. Unfolding follows a header when there is one.
    """
    reply = _ask("Passes [1], or legacy: ").strip().lower()
    if reply == "":
        return False, None
    if reply == "legacy":
        return True, None
    if reply == "multiscale":
        return False, 1
    if reply.isdigit():
        passes = int(reply)
        if 1 <= passes <= MAX_PASSES:
            return False, passes
    print(f"Enter a pass count from 1 to {MAX_PASSES}, or legacy.")
    return None


def _menu_settings(decrypting, key, legacy, passes):
    """Settings for one menu fold or unfold."""
    return {
        "decrypting": decrypting,
        "key": key,
        "folds": None,
        "binary": False,
        "header": False,
        "raw": False,
        "legacy": legacy,
        "passes": passes,
    }


def _menu_text(decrypting, show_map):
    label = "Folded text: " if decrypting else "Text: "
    text = _ask(label)
    if text == "":
        print("No text entered.")
        return
    key = _ask_key()
    chosen = _menu_geometry()
    if chosen is None:
        return
    legacy, passes = chosen
    try:
        out, subject, binary, folds, geometry, used = _transform_bytes(
            text.encode("utf-8"),
            _menu_settings(decrypting, key, legacy, passes),
            False,
        )
    except ValueError as exc:
        print(f"{NAME}: {exc}")
        return
    if binary:
        result = out
    else:
        result = out.decode("utf-8")
    if show_map:
        print(format_map(subject, key, folds, geometry=geometry, passes=used or 1))
        print()
    print(result)


def _menu_analysis():
    text = _ask("Text: ")
    if text == "":
        print("No text entered.")
        return
    key = _ask_key()
    chosen = _menu_geometry()
    if chosen is None:
        return
    legacy, passes = chosen
    if legacy:
        print(format_analysis(text, key))
        print()
        print(scramble(text, key))
        return
    used = 1 if passes is None else passes
    print(format_analysis(text, key, geometry=GEOMETRY_MULTISCALE, passes=used))
    print()
    print(scramble_multiscale(text, key, used))


def _menu_repeat():
    raw = _ask("Text, or a length such as 16: ")
    if raw.strip() == "":
        print("No text entered.")
        return
    key = _ask_key()
    chosen = _menu_geometry()
    if chosen is None:
        return
    legacy, passes = chosen
    if raw.strip().isdigit():
        specimen = int(raw.strip())
    else:
        specimen = raw
    if legacy:
        print(format_repeat(specimen, key))
        return
    print(format_repeat(
        specimen,
        key,
        geometry=GEOMETRY_MULTISCALE,
        passes=1 if passes is None else passes,
    ))


def _menu_custom():
    print(fold_legend())
    spec = _ask("Fold sequence: ")
    try:
        folds = parse_folds(spec)
    except ValueError as exc:
        print(f"{NAME}: {exc}")
        return
    kind = _ask("Fold or unfold? [F/u]: ").strip().lower()
    unfolding = kind in ("u", "unfold")
    text = _ask("Folded text: " if unfolding else "Text: ")
    if text == "":
        print("No text entered.")
        return
    if unfolding:
        plain = restore(text, folds=folds)
        result = plain
    else:
        plain = text
        result = scramble(text, folds=folds)
    print(format_analysis(plain, folds=folds))
    print()
    print(result)


def _menu_explore():
    raw = _ask("Length [16]: ").strip()
    if raw == "":
        length = 16
    elif raw.isdigit():
        length = int(raw)
    else:
        print("Enter a length, or press Enter for 16.")
        return
    key = _ask_key()
    other_key = _ask("Compare with a key (Enter to skip): ")
    other = None if other_key == "" else other_key
    print(format_multiscale_explore(length, key, 1, other))


def _menu_path(raw):
    """Accept a typed path, a quoted path, or a Terminal drag-and-drop path.

    Dragging a file into Terminal puts a backslash before spaces, commas,
    and other punctuation. Those escapes are undone when the written path
    is not already a file. On Windows the backslashes are separators and
    are left alone.
    """
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    path = Path(value).expanduser()
    if not path.exists() and "\\" in value and sys.platform != "win32":
        try:
            tokens = shlex.split(value)
        except ValueError:
            tokens = []
        if len(tokens) == 1:
            path = Path(tokens[0]).expanduser()
    return path


def _menu_file(decrypting):
    raw = _ask("File path (drag and drop works): ")
    source = _menu_path(raw)
    if not source.is_file():
        print(f"{source} is not a file.")
        return
    key = _ask_key()
    legacy = False
    passes = None
    if not decrypting:
        chosen = _menu_geometry()
        if chosen is None:
            return
        legacy, passes = chosen
    kind = _ask("Text or bytes? [T/b]: ").strip().lower()
    binary = kind in ("b", "byte", "bytes", "binary")
    data = source.read_bytes()
    settings = {
        "decrypting": decrypting,
        "key": key,
        "folds": None,
        "binary": binary,
        "header": False,
        "raw": False,
        "legacy": legacy,
        "passes": passes,
    }
    try:
        out, _subject, _binary, _used, _geometry, _passes = _transform_bytes(
            data, settings, True
        )
    except ValueError as exc:
        print(f"{NAME}: {exc}")
        return
    suggested = sibling_path(source, decrypting)
    print(f"Suggested file: {suggested}")
    reply = _ask("Press Enter to use it, or type another path: ")
    destination = suggested if reply.strip() == "" else _menu_path(reply)
    if destination.exists():
        reply = _ask(f"{destination} already exists. Replace it? [y/N] ")
        if reply.strip().lower() not in ("y", "yes"):
            print(f"Left {destination} unchanged.")
            return
    try:
        _refuse_same_file(source, destination)
        _write_file(destination, out)
    except OSError as exc:
        print(f"{NAME}: {exc}")
        return
    print(f"Wrote {destination}")


def _menu_folder(decrypting):
    """Pack a folder, or restore a package to a new folder."""
    try:
        if decrypting:
            source = _menu_path(_ask("Package path (drag and drop works): "))
            key = _ask_key()
            reply = _ask(
                "Restore into folder path (Enter = original name beside the package): "
            ).strip()
            output = None if reply == "" else _menu_path(reply)
            settings = {
                "decrypting": True,
                "key": key,
                "folds": None,
                "legacy": False,
                "passes": None,
                "output_name": None if output is None else str(output),
                "force": False,
                "raw": False,
            }
            result = decode_folder(source, settings)
            print(f"Restored folder: {result}")
            return
        print("The folder is stored in one archive, then folded as one message.")
        source = _menu_path(_ask("Folder path (drag and drop works): "))
        key = _ask_key()
        chosen = _menu_geometry()
        if chosen is None:
            return
        legacy, passes = chosen
        default = source.with_name(source.name + ".tess")
        print(f"Suggested package: {default}")
        reply = _ask("Press Enter to use it, or type another path: ")
        destination = default if reply.strip() == "" else _menu_path(reply)
        force = False
        if destination.exists() or destination.is_symlink():
            answer = _ask(f"{destination} already exists. Replace it? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print(f"Left {destination} unchanged.")
                return
            force = True
        settings = {
            "decrypting": False,
            "key": key,
            "folds": None,
            "legacy": legacy,
            "passes": passes,
            "output_name": str(destination),
            "force": force,
            "raw": False,
        }
        result = encode_folder(source, settings)
        print(f"Wrote {result}")
    except ValueError as exc:
        print(f"{NAME}: {exc}")
    except OSError as exc:
        print(f"{NAME}: {exc}")


def numbered_menu():
    """Interactive fold, unfold, analysis, and experiments."""
    print("TESSERACT FOLD — geometric folds of a 4D hypercube")
    print("This rearranges symbols. It does not hide them from someone")
    print("who has this program and the key. Enter :back to cancel a step.")
    while True:
        print()
        print("  1. Fold text")
        print("  2. Unfold text")
        print("  3. Fold a file")
        print("  4. Unfold a file")
        print("  5. Show a fold map")
        print("  6. Fold analysis")
        print("  7. Repeated-fold experiment")
        print("  8. Custom fold sequence")
        print("  9. Permutation explorer")
        print(" 10. Fold a folder")
        print(" 11. Unfold a folder")
        print("  0. Exit")
        try:
            choice = _ask("Choice: ").strip()
        except _MenuBack:
            continue
        except _MenuExit:
            return 0
        try:
            if choice == "0":
                return 0
            if choice == "1":
                _menu_text(False, False)
            elif choice == "2":
                _menu_text(True, False)
            elif choice == "3":
                _menu_file(False)
            elif choice == "4":
                _menu_file(True)
            elif choice == "5":
                _menu_text(False, True)
            elif choice == "6":
                _menu_analysis()
            elif choice == "7":
                _menu_repeat()
            elif choice == "8":
                _menu_custom()
            elif choice == "9":
                _menu_explore()
            elif choice == "10":
                _menu_folder(False)
            elif choice == "11":
                _menu_folder(True)
            else:
                print("Choose 0 through 11.")
        except _MenuBack:
            print("Canceled.")
        except _MenuExit:
            return 0
        except OSError as exc:
            print(f"{NAME}: {exc}")
        except KeyboardInterrupt:
            print(file=sys.stderr)
            return 130


def main(argv=None):
    """Run the program. Return an exit status."""
    if argv is None:
        argv = sys.argv
    try:
        return _main(argv)
    except KeyboardInterrupt:
        print(file=sys.stderr)
        return 130
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
