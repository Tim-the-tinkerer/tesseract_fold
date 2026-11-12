#!/usr/bin/env python3
"""Checks for tesseract_fold.py. Run: python3 test_tesseract_fold.py"""

import hashlib
import io
import os
import random
import shlex
import stat
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tesseract_fold

# FNV-1a 64 of "", "a", and "foobar". Public test vectors.
FNV_EMPTY = 0xCBF29CE484222325
FNV_A = 0xAF63DC4C8601EC8C
FNV_FOOBAR = 0x85944171F73967E8

HELLO = "lloeH"
KEYED_HELLO = "oHell"


class PipeIn:
    """Standard input that is not a terminal."""

    def __init__(self, data):
        self.buffer = io.BytesIO(data)

    def isatty(self):
        return False


class ScriptedIn:
    """A fake terminal that returns scripted lines, then end of file."""

    def __init__(self, lines):
        self._lines = list(lines)

    def isatty(self):
        return True

    def readline(self):
        if not self._lines:
            return ""
        return self._lines.pop(0)


class CapturedOut:
    """Stdout that accepts text and raw bytes in one buffer."""

    def __init__(self, tty=False):
        self.buffer = io.BytesIO()
        self.encoding = "utf-8"
        self._tty = tty

    def write(self, text):
        self.buffer.write(text.encode("utf-8"))
        return len(text)

    def flush(self):
        pass

    def isatty(self):
        return self._tty

    def close(self):
        pass


def run(argv, stdin=None, tty=False):
    stdout = CapturedOut(tty)
    stderr = io.StringIO()
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    if stdin is not None:
        sys.stdin = stdin
    sys.stdout = stdout
    try:
        with redirect_stderr(stderr):
            code = tesseract_fold.main(["tesseract_fold.py", *argv])
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout
    return code, stdout.buffer.getvalue(), stderr.getvalue()


class GeometryTest(unittest.TestCase):
    def test_catalog_has_32_folds(self):
        self.assertEqual(len(tesseract_fold.CATALOG), 32)
        kinds = {fold[0] for fold in tesseract_fold.CATALOG}
        self.assertEqual(kinds, {"hinge", "mirror", "diagonal", "half"})

    def test_canonical_folds_are_the_six_documented_moves(self):
        self.assertEqual(
            tesseract_fold.CANONICAL,
            (
                ("hinge", 0, 1, 1),
                ("hinge", 2, 3, 1),
                ("hinge", 0, 2, 1),
                ("hinge", 1, 3, 1),
                ("mirror", 3),
                ("diagonal", 0, 3),
            ),
        )

    def test_side_follows_the_hypercube(self):
        self.assertEqual(tesseract_fold.side_for(0), 2)
        self.assertEqual(tesseract_fold.side_for(1), 2)
        self.assertEqual(tesseract_fold.side_for(16), 2)
        self.assertEqual(tesseract_fold.side_for(17), 4)
        self.assertEqual(tesseract_fold.side_for(256), 4)
        self.assertEqual(tesseract_fold.side_for(257), 8)
        with self.assertRaises(ValueError):
            tesseract_fold.side_for(-1)
        with self.assertRaises(TypeError):
            tesseract_fold.side_for(True)
        with self.assertRaises(ValueError):
            tesseract_fold.side_for(tesseract_fold.MAX_SIDE ** 4 + 1)

    def test_index_round_trip_on_one_tesseract(self):
        for index in range(16):
            coord = tesseract_fold.index_to_coord(index, 2)
            self.assertEqual(tesseract_fold.coord_to_index(coord, 2), index)
            self.assertEqual(len(coord), 4)
            self.assertTrue(all(value in (0, 1) for value in coord))

    def test_hinge_is_a_counterclockwise_quarter_turn(self):
        coord = [0, 0, 5, 7]
        tesseract_fold.apply_fold(coord, ("hinge", 0, 1, 1), 2)
        self.assertEqual(coord, [1, 0, 5, 7])
        tesseract_fold.apply_fold(coord, ("hinge", 0, 1, 1), 2)
        self.assertEqual(coord, [1, 1, 5, 7])
        tesseract_fold.apply_fold(coord, ("hinge", 0, 1, 1), 2)
        self.assertEqual(coord, [0, 1, 5, 7])
        tesseract_fold.apply_fold(coord, ("hinge", 0, 1, 1), 2)
        self.assertEqual(coord, [0, 0, 5, 7])

    def test_mirror_flips_one_axis(self):
        coord = [0, 1, 0, 1]
        tesseract_fold.apply_fold(coord, ("mirror", 0), 4)
        self.assertEqual(coord, [3, 1, 0, 1])
        tesseract_fold.apply_fold(coord, ("mirror", 0), 4)
        self.assertEqual(coord, [0, 1, 0, 1])

    def test_diagonal_swaps_two_axes(self):
        coord = [1, 2, 3, 0]
        tesseract_fold.apply_fold(coord, ("diagonal", 0, 3), 4)
        self.assertEqual(coord, [0, 2, 3, 1])
        tesseract_fold.apply_fold(coord, ("diagonal", 0, 3), 4)
        self.assertEqual(coord, [1, 2, 3, 0])

    def test_half_fold_is_idle_on_one_tesseract_and_swaps_a_slab(self):
        for index in range(16):
            coord = tesseract_fold.index_to_coord(index, 2)
            original = list(coord)
            tesseract_fold.apply_fold(coord, ("half", 0, 1), 2)
            self.assertEqual(coord, original)
        upper = [2, 1, 1, 1]
        tesseract_fold.apply_fold(upper, ("half", 0, 1), 4)
        self.assertEqual(upper, [3, 1, 1, 1])
        lower = [0, 1, 1, 1]
        tesseract_fold.apply_fold(lower, ("half", 0, 0), 4)
        self.assertEqual(lower, [1, 1, 1, 1])
        untouched = [0, 1, 1, 1]
        tesseract_fold.apply_fold(untouched, ("half", 0, 1), 4)
        self.assertEqual(untouched, [0, 1, 1, 1])

    def test_check_folds_accepts_the_geometry(self):
        self.assertEqual(tesseract_fold.check_folds(), [])

    def test_fnv_vectors(self):
        self.assertEqual(tesseract_fold.fnv1a_64(b""), FNV_EMPTY)
        self.assertEqual(tesseract_fold.fnv1a_64(b"a"), FNV_A)
        self.assertEqual(tesseract_fold.fnv1a_64(b"foobar"), FNV_FOOBAR)

    def test_key_picks_four_to_seven_folds(self):
        self.assertEqual(len(tesseract_fold.fold_plan("")), 6)
        for key in ("a", "paper", "xyz", "0", "a longer phrase"):
            count = len(tesseract_fold.fold_plan(key))
            self.assertIn(count, (4, 5, 6, 7))
            self.assertEqual(tesseract_fold.fold_plan(key), tesseract_fold.fold_plan(key))
        with self.assertRaises(TypeError):
            tesseract_fold.fold_plan(None)


class ScrambleTest(unittest.TestCase):
    def test_hello_uses_the_canonical_folds(self):
        self.assertEqual(tesseract_fold.scramble("Hello"), HELLO)
        self.assertEqual(tesseract_fold.restore(HELLO), "Hello")
        self.assertEqual(tesseract_fold.scramble("Hello", "paper"), KEYED_HELLO)
        self.assertEqual(tesseract_fold.restore(KEYED_HELLO, "paper"), "Hello")

    def test_ranks_are_a_permutation(self):
        lengths = (0, 1, 2, 15, 16, 17, 255, 256, 257, 1000)
        for length in lengths:
            for key in ("", "paper", "tesseract"):
                dest = tesseract_fold.destination_ranks(
                    length, tesseract_fold.fold_plan(key)
                )
                self.assertEqual(sorted(dest), list(range(length)))

    def test_round_trip_keeps_every_symbol(self):
        texts = (
            "",
            "A",
            "Hello",
            "Hello, World!",
            "abπ✓\n",
            "a" * 17,
            "b" * 256,
            "c" * 257,
            "d" * 1000,
            "line\r\nline",
        )
        keys = ("", "paper", "fold", "a longer phrase with spaces")
        for text in texts:
            for key in keys:
                folded = tesseract_fold.scramble(text, key)
                self.assertEqual(Counter(folded), Counter(text))
                self.assertEqual(tesseract_fold.restore(folded, key), text)
        raw = bytes(range(256)) + b"\xff\x00"
        for key in keys:
            folded = tesseract_fold.scramble(raw, key)
            self.assertEqual(Counter(folded), Counter(raw))
            self.assertEqual(tesseract_fold.restore(folded, key), raw)

    def test_a_second_fold_is_not_decrypting(self):
        once = tesseract_fold.scramble("Hello")
        twice = tesseract_fold.scramble(once)
        self.assertNotEqual(twice, "Hello")
        self.assertNotEqual(tesseract_fold.restore(twice), "Hello")

    def test_the_key_changes_the_arrangement(self):
        self.assertNotEqual(
            tesseract_fold.scramble("Hello", "paper"),
            tesseract_fold.scramble("Hello"),
        )
        folded = tesseract_fold.scramble("Hello", "paper")
        self.assertNotEqual(tesseract_fold.restore(folded, "other"), "Hello")

    def test_unicode_moves_as_characters_and_bytes_move_as_bytes(self):
        text = "abπ"
        folded = tesseract_fold.scramble(text)
        self.assertEqual(len(folded), 3)
        self.assertEqual(Counter(folded), Counter(text))
        raw = text.encode("utf-8")
        self.assertGreater(len(raw), 3)
        self.assertNotEqual(tesseract_fold.scramble(raw), folded.encode("utf-8"))
        self.assertEqual(tesseract_fold.restore(tesseract_fold.scramble(raw)), raw)

    def test_map_reading_matches_the_fold(self):
        for text in ("Hello", "abcdefghijklmnopq", "A B", "A\nB"):
            for key in ("", "paper"):
                folded = tesseract_fold.scramble(text, key)
                self.assertTrue(
                    tesseract_fold.format_map(text, key).endswith(
                        "Read in coordinate order:\n" + folded
                    )
                )
        raw = bytes(range(20))
        folded = tesseract_fold.scramble(raw, "paper")
        self.assertTrue(
            tesseract_fold.format_map(raw, "paper").endswith(
                "Read in coordinate order:\n" + folded.hex(" ")
            )
        )

    def test_map_marks_a_space(self):
        self.assertIn("\u2423", tesseract_fold.format_map("A B", ""))
        self.assertIn("\u21b5", tesseract_fold.format_map("A\n", ""))

    def test_header_round_trip(self):
        packed = tesseract_fold.pack_document(HELLO, "", False, True)
        self.assertTrue(packed.startswith(b"TESSERACT-FOLD/1 key=0 mode=text\n"))
        key_used, binary, digest, folds, geometry, passes, payload = tesseract_fold.split_header(packed)
        self.assertFalse(key_used)
        self.assertFalse(binary)
        self.assertIsNone(digest)
        self.assertIsNone(folds)
        self.assertEqual(geometry, "legacy")
        self.assertIsNone(passes)
        self.assertEqual(payload, HELLO.encode("utf-8"))
        keyed = tesseract_fold.pack_document(b"\xff", "paper", True, True)
        key_used, binary, digest, folds, geometry, passes, payload = tesseract_fold.split_header(keyed)
        self.assertTrue(key_used)
        self.assertTrue(binary)
        self.assertIsNone(digest)
        self.assertIsNone(folds)
        self.assertEqual(geometry, "legacy")
        self.assertIsNone(passes)
        self.assertEqual(payload, b"\xff")
        with self.assertRaises(ValueError):
            tesseract_fold.unpack_document(keyed, "", True, False)
        with self.assertRaises(ValueError):
            tesseract_fold.unpack_document(packed, "paper", False, False)

    def test_menu_path_reads_a_dragged_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "how Pirate Captain Jankface, got his unique name.txt"
            source.write_text("Hello", encoding="utf-8")
            dragged = source.parent.as_posix() + "/" + "".join(
                "\\" + char if char in " ,\\" else char for char in source.name
            )
            self.assertIn(r"\,", dragged)
            self.assertEqual(tesseract_fold._menu_path(dragged), source)
            self.assertEqual(tesseract_fold._menu_path(shlex.quote(str(source))), source)
            self.assertEqual(tesseract_fold._menu_path(str(source)), source)
        missing = tesseract_fold._menu_path(
            r"/tmp/how\ Pirate\ Captain\ Jankface\,\ got\ his\ unique\ name.txt"
        )
        self.assertEqual(
            missing.name,
            "how Pirate Captain Jankface, got his unique name.txt",
        )

    def test_sibling_names(self):
        note = Path("note.txt")
        folded = tesseract_fold.sibling_path(note, False)
        self.assertEqual(folded.name, "note.tess.txt")
        self.assertEqual(tesseract_fold.sibling_path(folded, True).name, "note.txt")
        plain = tesseract_fold.sibling_path(note, True)
        self.assertEqual(plain.name, "note.plain.txt")
        archive = Path("archive.tess")
        self.assertEqual(tesseract_fold.sibling_path(archive, True).name, "archive")


class CommandTest(unittest.TestCase):
    def test_help_exits_0(self):
        code, out, err = run(["--help"])
        self.assertEqual(code, 0)
        self.assertIn(HELLO.encode("utf-8"), out)
        self.assertEqual(err, "")
        code, out, err = run(["-h"])
        self.assertEqual(code, 0)
        self.assertIn(b"Usage:", out)

    def test_words_gain_a_newline_that_is_not_folded(self):
        code, out, err = run(["Hello"])
        self.assertEqual(code, 0)
        folded = tesseract_fold.scramble_multiscale("Hello")
        self.assertEqual(out, (folded + "\n").encode("utf-8"))
        self.assertEqual(err, "")
        code, out, err = run(["--decrypt", folded])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"Hello\n")
        code, out, err = run(["--legacy", "Hello"])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"lloeH\n")
        code, out, err = run(["--legacy", "--decrypt", HELLO])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"Hello\n")

    def test_a_pipe_keeps_every_byte(self):
        code, out, err = run([], PipeIn(b"Hello"))
        self.assertEqual(code, 0)
        folded = tesseract_fold.scramble_multiscale("Hello").encode("utf-8")
        self.assertEqual(out, folded)
        self.assertEqual(err, "")
        code, out, err = run(["--decrypt"], PipeIn(folded))
        self.assertEqual(code, 0)
        self.assertEqual(out, b"Hello")
        code, out, err = run(["--legacy"], PipeIn(b"Hello"))
        self.assertEqual(out, b"lloeH")
        code, out, err = run(["--legacy", "--decrypt"], PipeIn(b"lloeH"))
        self.assertEqual(out, b"Hello")

    def test_key_flag_forms_agree(self):
        code, spaced, err = run(["--key", "paper", "Hello"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        code, joined, err = run(["--key=paper", "Hello"])
        self.assertEqual(code, 0)
        self.assertEqual(spaced, joined)
        expected = (tesseract_fold.scramble_multiscale("Hello", "paper") + "\n").encode("utf-8")
        self.assertEqual(spaced, expected)
        code, out, err = run(["--legacy", "--key", "paper", "Hello"])
        self.assertEqual(out, b"oHell\n")
        code, out, err = run(["--legacy", "-k", "paper", "--decrypt", KEYED_HELLO])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"Hello\n")
        self.assertEqual(err, "")

    def test_bad_arguments_exit_2(self):
        for argv in (
            ["--nope"],
            ["--key"],
            ["--output"],
            ["--file"],
            ["--header", "--raw", "Hello"],
            ["--binary", "--text", "Hello"],
            ["--menu", "--decrypt"],
            ["--check", "Hello"],
            ["--check", "--map"],
            ["--legacy", "--passes", "2", "Hello"],
            ["--folds", "mx", "--passes", "2", "Hello"],
            ["--passes", "0", "Hello"],
            ["--passes", "17", "Hello"],
        ):
            code, out, err = run(argv)
            self.assertEqual(code, 2, argv)
            self.assertEqual(out, b"", argv)
            self.assertIn("usage:", err, argv)
            self.assertIn("tesseract_fold.py:", err, argv)

    def test_check_command(self):
        code, out, err = run(["--check"])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"")
        self.assertIn("check ok", err)
        self.assertIn("Hello -> lloeH", err)

    def test_map_does_not_change_the_result(self):
        code, out, err = run(["--legacy", "--map", "Hello"])
        self.assertEqual(code, 0)
        self.assertEqual(out, b"lloeH\n")
        self.assertIn("TESSERACT FOLD MAP", err)
        self.assertIn("quarter-turn counterclockwise in the xy plane", err)
        self.assertIn("lloeH", err)
        code, out, err = run(["--map", "Hello"])
        self.assertEqual(code, 0)
        folded = tesseract_fold.scramble_multiscale("Hello")
        self.assertEqual(out, (folded + "\n").encode("utf-8"))
        self.assertIn("multiscale geometry, 1 pass", err)
        self.assertIn("Read in coordinate order:\n" + folded, err)

    def test_header_on_typed_text_and_its_decrypt(self):
        code, out, err = run(["--header", "Hello"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertTrue(out.startswith(b"TESSERACT-FOLD/4 key=0 mode=text sha256="))
        self.assertIn(b"geometry=multiscale passes=1\n", out)
        code, back, err = run(["--decrypt"], PipeIn(out))
        self.assertEqual(code, 0)
        self.assertEqual(back, b"Hello")
        self.assertEqual(err, "")
        code, out, err = run(["--legacy", "--header", "Hello"])
        self.assertTrue(out.startswith(b"TESSERACT-FOLD/2 key=0 mode=text sha256="))
        self.assertTrue(out.endswith(b"lloeH"))
        code, back, err = run(["--decrypt"], PipeIn(out))
        self.assertEqual(back, b"Hello")

    def test_missing_path_is_text(self):
        code, out, err = run(["missing-file.txt"])
        self.assertEqual(code, 0)
        self.assertIn("not a file", err)
        self.assertTrue(out.endswith(b"\n"))
        folded = tesseract_fold.scramble_multiscale("missing-file.txt")
        self.assertEqual(out, (folded + "\n").encode("utf-8"))

    def test_double_dash_forces_text(self):
        code, out, err = run(["--", "--decrypt"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        folded = tesseract_fold.scramble_multiscale("--decrypt")
        self.assertEqual(out, (folded + "\n").encode("utf-8"))

    def test_text_file_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_bytes("Hello\nπ\n".encode("utf-8"))
            code, out, err = run([str(source)])
            self.assertEqual(code, 0)
            self.assertEqual(out, b"")
            dest = folder / "note.tess.txt"
            self.assertTrue(dest.is_file(), err)
            stored = dest.read_bytes()
            self.assertTrue(stored.startswith(b"TESSERACT-FOLD/4 key=0 mode=text sha256="))
            self.assertIn(b"geometry=multiscale passes=1\n", stored)
            self.assertEqual(source.read_bytes(), "Hello\nπ\n".encode("utf-8"))
            code, out, err = run(["--decrypt", str(dest)])
            self.assertEqual(code, 1)
            self.assertIn("already exists", err)
            restored = folder / "back.txt"
            code, out, err = run(["--decrypt", str(dest), "--output", str(restored)])
            self.assertEqual(code, 0, err)
            self.assertEqual(restored.read_bytes(), source.read_bytes())

    def test_raw_file_has_no_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            dest = folder / "note.tess.txt"
            code, out, err = run(["--legacy", "--raw", str(source)])
            self.assertEqual(code, 0, err)
            self.assertEqual(dest.read_bytes(), HELLO.encode("utf-8"))
            back = folder / "plain.txt"
            code, out, err = run(
                ["--decrypt", "--legacy", "--raw", str(dest), "--output", str(back)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(back.read_text(encoding="utf-8"), "Hello")

    def test_binary_round_trip_and_stdout(self):
        payload = bytes(range(256)) + b"\xff\xfe"
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "data.bin"
            source.write_bytes(payload)
            code, out, err = run(["--binary", str(source)])
            self.assertEqual(code, 0, err)
            stored = (folder / "data.tess.bin").read_bytes()
            self.assertTrue(stored.startswith(b"TESSERACT-FOLD/4 key=0 mode=bin sha256="))
            self.assertIn(b"passes=1\n", stored)
            code, out, err = run(["--decrypt"], PipeIn(stored))
            self.assertEqual(code, 0, err)
            self.assertEqual(out, payload)
            keyed = folder / "keyed.bin"
            code, out, err = run(
                ["--binary", "--key", "paper", str(source), "--output", str(keyed)]
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(
                keyed.read_bytes().startswith(b"TESSERACT-FOLD/4 key=1 mode=bin sha256=")
            )
            code, out, err = run(["--decrypt", str(keyed), "--output", str(folder / "nope.bin")])
            self.assertEqual(code, 1)
            self.assertIn("used a key", err)
            back = folder / "back.bin"
            code, out, err = run(
                ["--decrypt", "--key", "paper", str(keyed), "--output", str(back)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(back.read_bytes(), payload)

    def test_output_replaces_and_refuses_the_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            dest = folder / "out" / "folded.txt"
            dest.parent.mkdir()
            dest.write_text("old", encoding="utf-8")
            code, out, err = run([str(source), "--output", str(dest)])
            self.assertEqual(code, 1)
            self.assertIn("--force", err)
            self.assertEqual(dest.read_text(encoding="utf-8"), "old")
            code, out, err = run([str(source), "--output", str(dest), "--force"])
            self.assertEqual(code, 0, err)
            self.assertEqual(out, b"")
            self.assertTrue(
                dest.read_bytes().endswith(
                    tesseract_fold.scramble_multiscale("Hello").encode("utf-8")
                )
            )
            code, out, err = run([str(source), "--output", str(source), "--force"])
            self.assertEqual(code, 1)
            self.assertIn("refusing to replace", err)
            self.assertEqual(source.read_text(encoding="utf-8"), "Hello")

    def test_a_directory_is_folded_beside_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            box = folder / "Box"
            box.mkdir()
            (box / "note.txt").write_text("Hello\n", encoding="utf-8")
            before = (box / "note.txt").read_bytes()
            code, out, err = run([str(box)])
            self.assertEqual(code, 0, err)
            self.assertEqual(out, b"")
            package = folder / "Box.tess"
            self.assertTrue(package.is_file(), err)
            self.assertTrue(package.read_bytes().startswith(b"TESSERACT-FOLD-FOLDER/1 "))
            self.assertEqual((box / "note.txt").read_bytes(), before)
            self.assertFalse((folder.parent / "Box.tess").exists())
            restored = folder / "Box-restored"
            code, out, err = run(
                ["--decrypt", str(package), "--output", str(restored)]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("restored", err)
            self.assertEqual((restored / "note.txt").read_text(encoding="utf-8"), "Hello\n")
            self.assertEqual((box / "note.txt").read_bytes(), before)

    def test_two_files_and_one_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = folder / "a.txt"
            second = folder / "b.txt"
            first.write_text("Hello", encoding="utf-8")
            second.write_text("World", encoding="utf-8")
            code, out, err = run([str(first), str(second), "--output", str(folder / "one.txt")])
            self.assertEqual(code, 2)
            self.assertIn("--output needs a single file", err)
            code, out, err = run([str(first), str(second)])
            self.assertEqual(code, 0, err)
            self.assertTrue((folder / "a.tess.txt").is_file())
            self.assertTrue((folder / "b.tess.txt").is_file())

    def test_text_flag_does_not_read_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            old = os.getcwd()
            os.chdir(folder)
            try:
                code, out, err = run(["--text", "note.txt"])
            finally:
                os.chdir(old)
            self.assertEqual(code, 0, err)
            folded = tesseract_fold.scramble_multiscale("note.txt")
            self.assertEqual(out, (folded + "\n").encode("utf-8"))
            self.assertEqual(source.read_text(encoding="utf-8"), "Hello")
            self.assertFalse((folder / "note.tess.txt").exists())

    def test_utf8_error_names_binary_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "raw.bin"
            source.write_bytes(b"\xff\xfe")
            code, out, err = run([str(source)])
            self.assertEqual(code, 1)
            self.assertIn("--binary", err)
            self.assertEqual(out, b"")

    def test_menu_encrypts_and_decrypts_a_line(self):
        code, out, err = run(
            ["--menu"], ScriptedIn(["1\n", "Hello\n", "\n", "legacy\n", "0\n"])
        )
        self.assertEqual(code, 0, err)
        self.assertIn(b"lloeH", out)
        code, out, err = run(
            ["--menu"], ScriptedIn(["2\n", HELLO + "\n", "\n", "legacy\n", "0\n"])
        )
        self.assertEqual(code, 0, err)
        self.assertIn(b"Hello", out)
        folded = tesseract_fold.scramble_multiscale("Hello")
        code, out, err = run(
            ["--menu"], ScriptedIn(["1\n", "Hello\n", "\n", "\n", "0\n"])
        )
        self.assertEqual(code, 0, err)
        self.assertIn(folded.encode("utf-8"), out)
        code, out, err = run(
            ["--menu"], ScriptedIn(["2\n", folded + "\n", "\n", "\n", "0\n"])
        )
        self.assertEqual(code, 0, err)
        self.assertIn(b"Hello", out)

    def test_menu_back_cancels(self):
        code, out, err = run(["--menu"], ScriptedIn(["1\n", ":back\n", "0\n"]))
        self.assertEqual(code, 0, err)
        self.assertIn(b"Canceled.", out)
        self.assertNotIn(b"lloeH", out)

    def test_menu_end_of_input_exits_0(self):
        code, out, err = run(["--menu"], ScriptedIn([]))
        self.assertEqual(code, 0, err)

    def test_menu_says_fold(self):
        code, out, err = run(["--menu"], ScriptedIn(["0\n"]))
        self.assertEqual(code, 0, err)
        self.assertIn(b"Fold text", out)
        self.assertIn(b"Unfold text", out)
        self.assertIn(b"Permutation explorer", out)
        self.assertNotIn(b"Encrypt text", out)


class LaboratoryTest(unittest.TestCase):
    def test_canonical_names_and_a_mirror_pair(self):
        self.assertEqual(tesseract_fold.parse_folds("xy+, zw+, xz+, yw+, mw, dxw"), tesseract_fold.CANONICAL)
        self.assertEqual(
            tesseract_fold.parse_folds("#0"),
            (tesseract_fold.FOLD_NAMES["xy+"],),
        )
        folds = tesseract_fold.parse_folds("mx")
        order, lengths = tesseract_fold.permutation_order(
            tesseract_fold.destination_ranks(8, folds)
        )
        self.assertEqual(order, 2)
        self.assertIn(2, lengths)
        identity = tesseract_fold.parse_folds("mx,mx")
        self.assertEqual(
            tesseract_fold.destination_ranks(8, identity),
            list(range(8)),
        )
        with self.assertRaises(ValueError):
            tesseract_fold.parse_folds("spin")
        with self.assertRaises(ValueError):
            tesseract_fold.parse_folds("")

    def test_analysis_reports_a_reversal(self):
        report = tesseract_fold.format_analysis("Hello", folds=tesseract_fold.parse_folds("mx,mx"))
        self.assertIn("FOLD ANALYSIS", report)
        self.assertIn("the permutation is the original arrangement", report)
        self.assertIn("reversed some earlier displacement", report)
        self.assertIn("displacement increased", report)
        hello = tesseract_fold.format_analysis("Hello")
        self.assertIn("the permutation is not the original arrangement", hello)
        self.assertIn("order ", hello)
        self.assertIn("Symbol movement after each fold", hello)
        self.assertIn("cycles", hello)

    def test_repeated_fold_order_matches_applying_the_sequence(self):
        folds = tesseract_fold.CANONICAL
        text = "Hello"
        dest = tesseract_fold.destination_ranks(len(text), folds)
        order, _lengths = tesseract_fold.permutation_order(dest)
        self.assertGreater(order, 1)
        current = text
        for _ in range(order):
            current = tesseract_fold.scramble(current, folds=folds)
        self.assertEqual(current, text)
        current = text
        for _ in range(order - 1):
            current = tesseract_fold.scramble(current, folds=folds)
        self.assertNotEqual(current, text)
        report = tesseract_fold.format_repeat(text)
        self.assertIn(f"order {order}", report)
        self.assertIn("application 0: Hello", report)
        self.assertIn(f"application {order}: Hello", report)
        self.assertIn("lloeH", report)

    def test_quarter_turns_and_two_mirrors_are_the_same_permutation(self):
        spins = tesseract_fold.parse_folds("xy+,xy+,xy+,xy+")
        mirrors = tesseract_fold.parse_folds("mx,mx")
        self.assertTrue(tesseract_fold.same_permutation(16, spins, mirrors))
        self.assertTrue(tesseract_fold.same_permutation(17, spins, mirrors))
        report = tesseract_fold.format_explore(16, spins, mirrors, "the other fold sequence")
        self.assertIn("same permutation", report)
        self.assertIn("This length fills the hypercube.", report)
        different = tesseract_fold.format_explore(16, tesseract_fold.CANONICAL, mirrors)
        self.assertIn("different permutation", different)

    def test_paths_follow_hello(self):
        report = tesseract_fold.format_map("Hello")
        self.assertIn("Symbol paths", report)
        self.assertIn("[0] H  (0,0,0,0) ->", report)
        self.assertTrue(report.endswith("Read in coordinate order:\nlloeH"))

    def test_boundaries_and_random_bytes(self):
        lengths = (0, 1, 15, 16, 17, 255, 256, 257, 4095, 4096, 4097)
        for length in lengths:
            self.assertEqual(
                tesseract_fold.side_for(length) ** 4 >= max(length, 1) or length == 0,
                True,
            )
            blob = bytes(index % 256 for index in range(length))
            for key in ("", "paper"):
                self.assertEqual(
                    tesseract_fold.restore(tesseract_fold.scramble(blob, key), key),
                    blob,
                )
        rng = random.Random(20261110)
        sample = bytes(rng.getrandbits(8) for _ in range(1500))
        folded = tesseract_fold.scramble(sample, "laboratory")
        self.assertEqual(tesseract_fold.restore(folded, "laboratory"), sample)
        self.assertEqual(Counter(folded), Counter(sample))
        text = "héllo\nπ\n🎲\ne\u0301"
        self.assertEqual(
            tesseract_fold.restore(tesseract_fold.scramble(text, "π"), "π"),
            text,
        )
        self.assertEqual(Counter(tesseract_fold.scramble(text, "π")), Counter(text))

    def test_custom_folds_round_trip_on_the_command_line(self):
        code, out, err = run(["--folds", "xy+,zw+,xz+,yw+,mw,dxw", "Hello"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, b"lloeH\n")
        code, out, err = run(["--folds", "mx,mx", "--decrypt", "Hello"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, b"Hello\n")
        code, out, err = run(["--key", "paper", "--folds", "mx"])
        self.assertEqual(code, 2)
        self.assertIn("not both", err)

    def test_analyze_and_repeat_and_explore_commands(self):
        code, out, err = run(["--analyze", "Hello"])
        self.assertEqual(code, 0, err)
        folded = tesseract_fold.scramble_multiscale("Hello")
        self.assertEqual(out, (folded + "\n").encode("utf-8"))
        self.assertIn("FOLD ANALYSIS", err)
        self.assertIn("Scramble quality", err)
        self.assertIn("multiscale geometry, 1 pass", err)
        self.assertIn("After each pass", err)
        self.assertIn("neighboring pairs", err)
        code, out, err = run(["--legacy", "--analyze", "Hello"])
        self.assertEqual(out, b"lloeH\n")
        self.assertIn("Symbol movement after each fold", err)
        self.assertIn("neighboring pairs", err)
        code, out, err = run(["--repeat", "Hello"])
        self.assertEqual(code, 0, err)
        self.assertIn(b"REPEATED FOLD", out)
        self.assertIn(b"multiscale geometry, 1 pass", out)
        self.assertIn(b"application 0: Hello", out)
        self.assertEqual(err, "")
        code, out, err = run(["--legacy", "--repeat", "Hello"])
        self.assertIn(b"lloeH", out)
        code, out, err = run(
            [
                "--explore",
                "--length",
                "16",
                "--folds",
                "xy+,xy+,xy+,xy+",
                "--compare-folds",
                "mx,mx",
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertIn(b"same permutation", out)
        self.assertIn(b"PERMUTATION EXPLORER", out)
        code, out, err = run(["--explore", "--length", "16", "--compare="])
        self.assertEqual(code, 0, err)
        self.assertIn(b"same permutation", out)
        self.assertIn(b"multiscale geometry, 1 pass", out)
        code, out, err = run(["--legacy", "--explore", "--length", "16", "--compare="])
        self.assertEqual(code, 0, err)
        self.assertIn(b"same permutation", out)
        self.assertIn(b"canonical folds", out)

    def test_trace_selects_a_symbol(self):
        code, out, err = run(["--legacy", "--map", "--trace", "0,4", "Hello"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, b"lloeH\n")
        self.assertIn("[0] H", err)
        self.assertIn("[4] o", err)
        self.assertNotIn("[1] e", err)

    def test_version_1_header_still_unfolds(self):
        payload = tesseract_fold.scramble("Hello").encode("utf-8")
        blob = b"TESSERACT-FOLD/1 key=0 mode=text\n" + payload
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "old.tess.txt"
            source.write_bytes(blob)
            dest = Path(tmp) / "back.txt"
            code, out, err = run(["--decrypt", str(source), "--output", str(dest)])
            self.assertEqual(code, 0, err)
            self.assertEqual(dest.read_text(encoding="utf-8"), "Hello")

    def test_digest_rejects_the_wrong_key_and_a_damaged_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            folded = folder / "note.tess.txt"
            code, out, err = run(["--key", "paper", str(source)])
            self.assertEqual(code, 0, err)
            stored = folded.read_bytes()
            digest = hashlib.sha256(b"Hello").hexdigest().encode("ascii")
            self.assertIn(b"sha256=" + digest, stored)
            wrong = folder / "wrong.txt"
            code, out, err = run(
                ["--decrypt", "--key", "other", str(folded), "--output", str(wrong)]
            )
            self.assertEqual(code, 1)
            self.assertIn("digest", err)
            self.assertFalse(wrong.exists())
            damaged = bytearray(stored)
            damaged[-1] ^= 0x01
            bad = folder / "damaged.tess.txt"
            bad.write_bytes(damaged)
            code, out, err = run(
                ["--decrypt", "--key", "paper", str(bad), "--output", str(folder / "nope.txt")]
            )
            self.assertEqual(code, 1)
            self.assertIn("digest", err)
            self.assertFalse((folder / "nope.txt").exists())
            header = folder / "broken.tess.txt"
            header.write_bytes(b"TESSERACT-FOLD/2 key=0 mode=text sha256=abcd\nHello")
            code, out, err = run(["--decrypt", str(header), "--output", str(folder / "x.txt")])
            self.assertEqual(code, 1)
            self.assertIn("damaged header", err)
            self.assertFalse((folder / "x.txt").exists())

    def test_random_binary_file_round_trip(self):
        rng = random.Random(7)
        payload = bytes(rng.getrandbits(8) for _ in range(4097))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "blob.bin"
            source.write_bytes(payload)
            code, out, err = run(["--binary", "--key", "paper", str(source)])
            self.assertEqual(code, 0, err)
            stored = (folder / "blob.tess.bin").read_bytes()
            self.assertIn(hashlib.sha256(payload).hexdigest().encode("ascii"), stored)
            back = folder / "back.bin"
            code, out, err = run(
                ["--decrypt", "--key", "paper", str(folder / "blob.tess.bin"), "--output", str(back)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(back.read_bytes(), payload)

    def test_failed_write_leaves_the_destination_and_no_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out.txt"
            dest.write_bytes(b"old")
            real = os.replace

            def boom(*_args, **_kwargs):
                raise OSError("disk full")

            os.replace = boom
            try:
                with self.assertRaises(OSError):
                    tesseract_fold._write_file(dest, b"new-bytes")
            finally:
                os.replace = real
            self.assertEqual(dest.read_bytes(), b"old")
            self.assertEqual(list(Path(tmp).glob("*.partial")), [])
            tesseract_fold._write_file(dest, b"new-bytes")
            self.assertEqual(dest.read_bytes(), b"new-bytes")
            self.assertEqual(list(Path(tmp).glob("*.partial")), [])

    def test_terminal_asks_before_replacing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            dest = folder / "out.txt"
            dest.write_text("old", encoding="utf-8")
            code, out, err = run(
                [str(source), "--output", str(dest)],
                ScriptedIn(["n\n"]),
                tty=True,
            )
            self.assertEqual(code, 1)
            self.assertIn("Replace it?", err)
            self.assertEqual(dest.read_text(encoding="utf-8"), "old")
            code, out, err = run(
                [str(source), "--output", str(dest)],
                ScriptedIn(["y\n"]),
                tty=True,
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(
                dest.read_bytes().endswith(
                    tesseract_fold.scramble_multiscale("Hello").encode("utf-8")
                )
            )
            code, out, err = run(
                [str(source), "--output", str(dest), "--force"],
                ScriptedIn([]),
                tty=True,
            )
            self.assertEqual(code, 0, err)
            self.assertNotIn("Replace it?", err)

    def test_recorded_sequence_unfolds_without_passing_it_again(self):
        folds = tesseract_fold.parse_folds("mx,zw+")
        self.assertEqual(tesseract_fold.fold_spec(folds), "mx,zw+")
        self.assertEqual(
            tesseract_fold.fold_spec(tesseract_fold.parse_folds("#0")),
            "xy+",
        )
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            code, out, err = run(["--folds", "mx,zw+", str(source)])
            self.assertEqual(code, 0, err)
            stored = (folder / "note.tess.txt").read_bytes()
            self.assertTrue(stored.startswith(b"TESSERACT-FOLD/3 key=0 mode=text "))
            self.assertIn(b"folds=mx,zw+\n", stored)
            self.assertNotIn(b"key=1", stored)
            back = folder / "back.txt"
            code, out, err = run(
                ["--decrypt", str(folder / "note.tess.txt"), "--output", str(back)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(back.read_text(encoding="utf-8"), "Hello")
            wrong = folder / "wrong.txt"
            code, out, err = run(
                [
                    "--decrypt",
                    "--folds",
                    "mx",
                    str(folder / "note.tess.txt"),
                    "--output",
                    str(wrong),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("records folds mx,zw+", err)
            self.assertFalse(wrong.exists())
            code, out, err = run(
                [
                    "--decrypt",
                    "--folds",
                    "#0,zw+",
                    str(folder / "note.tess.txt"),
                    "--output",
                    str(folder / "same.txt"),
                ]
            )
            self.assertEqual(code, 1)
            self.assertFalse((folder / "same.txt").exists())
        code, out, err = run(["--header", "--folds", "mx", "Hello"])
        self.assertEqual(code, 0, err)
        self.assertIn(b"folds=mx\n", out)
        code, restored, err = run(["--decrypt"], PipeIn(out))
        self.assertEqual(code, 0, err)
        self.assertEqual(restored, b"Hello")
        code, out, err = run(["--force", "Hello"])
        self.assertEqual(code, 2)
        self.assertIn("--force needs --output", err)

    def test_menu_custom_sequence_can_unfold(self):
        folded = tesseract_fold.scramble("Hello", folds=tesseract_fold.parse_folds("mx"))
        code, out, err = run(
            ["--menu"],
            ScriptedIn(["8\n", "mx\n", "u\n", folded + "\n", "0\n"]),
        )
        self.assertEqual(code, 0, err)
        self.assertIn(b"Hello", out)
        self.assertIn(b"FOLD ANALYSIS", out)
        code, out, err = run(
            ["--menu"],
            ScriptedIn(["8\n", "mx,mx\n", "\n", "Hello\n", "0\n"]),
        )
        self.assertEqual(code, 0, err)
        self.assertIn(b"Hello", out)

    def test_multiscale_hello_is_not_the_legacy_fold(self):
        self.assertEqual(tesseract_fold.scramble_multiscale("Hello"), "lelHo")
        self.assertEqual(tesseract_fold.restore_multiscale("lelHo"), "Hello")
        self.assertNotEqual(
            tesseract_fold.scramble_multiscale("Hello", passes=2),
            "lelHo",
        )
        self.assertEqual(
            tesseract_fold.restore_multiscale(
                tesseract_fold.scramble_multiscale("Hello", "paper", 2),
                "paper",
                2,
            ),
            "Hello",
        )
        report = tesseract_fold.format_analysis("Hello")
        self.assertIn("Scramble quality", report)
        self.assertIn("longest preserved sequence", report)
        self.assertIn("mean displacement", report)

    def test_version_4_records_passes_and_rejects_a_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "note.txt"
            source.write_text("Hello", encoding="utf-8")
            code, out, err = run(["--passes", "2", "--key", "paper", str(source)])
            self.assertEqual(code, 0, err)
            stored = (folder / "note.tess.txt").read_bytes()
            self.assertTrue(stored.startswith(b"TESSERACT-FOLD/4 key=1 mode=text "))
            self.assertIn(b"geometry=multiscale passes=2\n", stored)
            self.assertNotIn(b"paper", stored)
            back = folder / "back.txt"
            code, out, err = run(
                [
                    "--decrypt",
                    "--key",
                    "paper",
                    str(folder / "note.tess.txt"),
                    "--output",
                    str(back),
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(back.read_text(encoding="utf-8"), "Hello")
            same = folder / "same.txt"
            code, out, err = run(
                [
                    "--decrypt",
                    "--key",
                    "paper",
                    "--passes",
                    "2",
                    str(folder / "note.tess.txt"),
                    "--output",
                    str(same),
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(same.read_text(encoding="utf-8"), "Hello")
            wrong = folder / "wrong.txt"
            code, out, err = run(
                [
                    "--decrypt",
                    "--key",
                    "paper",
                    "--passes",
                    "1",
                    str(folder / "note.tess.txt"),
                    "--output",
                    str(wrong),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("records 2 passes", err)
            self.assertFalse(wrong.exists())
            code, out, err = run(
                [
                    "--decrypt",
                    "--legacy",
                    "--key",
                    "paper",
                    str(folder / "note.tess.txt"),
                    "--output",
                    str(folder / "legacy.txt"),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("omit --legacy", err)
            self.assertFalse((folder / "legacy.txt").exists())
            legacy = folder / "old.txt"
            code, out, err = run(["--legacy", str(source), "--output", str(legacy)])
            self.assertEqual(code, 0, err)
            self.assertTrue(legacy.read_bytes().startswith(b"TESSERACT-FOLD/2 "))
            self.assertTrue(legacy.read_bytes().endswith(b"lloeH"))
            code, out, err = run(
                [
                    "--decrypt",
                    "--passes",
                    "1",
                    str(legacy),
                    "--output",
                    str(folder / "nope.txt"),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("legacy geometry", err)
            self.assertFalse((folder / "nope.txt").exists())
            digest = b"ab" * 32
            broken = folder / "broken.tess.txt"
            broken.write_bytes(
                b"TESSERACT-FOLD/4 key=0 mode=text sha256="
                + digest
                + b" geometry=multiscale passes=99\nHello"
            )
            code, out, err = run(
                ["--decrypt", str(broken), "--output", str(folder / "x.txt")]
            )
            self.assertEqual(code, 1)
            self.assertIn("damaged header", err)
            self.assertFalse((folder / "x.txt").exists())
        folded = tesseract_fold.scramble_multiscale("Hello", passes=2)
        code, out, err = run(["--raw", "--passes", "2", "Hello"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, (folded + "\n").encode("utf-8"))
        code, back, err = run(
            ["--decrypt", "--raw", "--passes", "2"],
            PipeIn(folded.encode("utf-8")),
        )
        self.assertEqual(back, b"Hello")
        code, back, err = run(["--decrypt", "--raw"], PipeIn(folded.encode("utf-8")))
        self.assertNotEqual(back, b"Hello")

    def test_tim_the_tinkerer_keeps_legacy_runs_and_multiscale_breaks_them(self):
        path = Path(__file__).resolve().parent / "testdata" / "Creation.txt"
        raw = path.read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "d4520302cac7d60a7754f5545591f35a9e03bf6a5113ce8864e8a082e41ac901",
        )
        text = raw.decode("utf-8")
        self.assertEqual(len(text), 1682)
        self.assertEqual(tesseract_fold.side_for(len(text)), 8)
        key = "Tim-the-tinkerer"
        plan = tesseract_fold.fold_plan(key)
        self.assertEqual(tesseract_fold.fold_spec(plan), "yw+,yz-,hy-,dyz,yw-,dyw")
        axes = set()
        for fold in plan:
            axes.update(tesseract_fold.axes_of(fold))
        self.assertNotIn(0, axes)
        dest = tesseract_fold.destination_ranks(len(text), plan)
        runs = tesseract_fold.preserved_runs(dest)
        self.assertEqual(sum(run - 1 for run in runs), 1471)
        self.assertEqual(max(runs), 8)
        self.assertEqual(tesseract_fold.windows_in_runs(runs, 8), 210)
        self.assertEqual(tesseract_fold.windows_in_runs(runs, 16), 0)
        legacy = tesseract_fold.scramble(text, key)
        self.assertEqual(tesseract_fold.restore(legacy, key), text)
        self.assertEqual(tesseract_fold.surviving_text_windows(text, legacy, 8), 352)
        lengths = []
        for salt in ("global-a", "local-8", "coarse-8", "global-b"):
            mixed = tesseract_fold.fold_plan_mixed(key, 0, salt)
            covered = set()
            for fold in mixed:
                covered.update(tesseract_fold.axes_of(fold))
            self.assertEqual(covered, {0, 1, 2, 3}, salt)
            lengths.append(len(mixed))
        self.assertEqual(lengths, [7, 7, 5, 5])
        self.assertNotEqual(
            tesseract_fold.fold_plan_mixed(key, 0, "global-a"),
            tesseract_fold.fold_plan_mixed(key, 1, "global-a"),
        )
        folded = tesseract_fold.scramble_multiscale(text, key, 1)
        self.assertEqual(tesseract_fold.restore_multiscale(folded, key, 1), text)
        ranks = tesseract_fold.multiscale_ranks(len(text), key, 1)
        runs = tesseract_fold.preserved_runs(ranks)
        self.assertEqual(sum(run - 1 for run in runs), 0)
        self.assertEqual(max(runs), 1)
        self.assertEqual(tesseract_fold.windows_in_runs(runs, 8), 0)
        self.assertEqual(tesseract_fold.windows_in_runs(runs, 16), 0)
        self.assertEqual(tesseract_fold.surviving_text_windows(text, folded, 4), 30)
        self.assertEqual(tesseract_fold.surviving_text_windows(text, folded, 8), 0)
        self.assertEqual(tesseract_fold.surviving_text_windows(text, folded, 12), 0)
        self.assertEqual(tesseract_fold.surviving_text_windows(text, folded, 16), 0)
        moved = [abs(ranks[index] - index) for index in range(len(ranks))]
        self.assertEqual(round(sum(moved) / len(moved), 1), 666.3)
        twice = tesseract_fold.scramble_multiscale(text, key, 2)
        self.assertNotEqual(twice, folded)
        self.assertEqual(tesseract_fold.restore_multiscale(twice, key, 2), text)


def _snapshot(root):
    """Relative path to ('dir', None) or ('file', bytes). Dot names are kept."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel_dir = current.relative_to(root).as_posix()
        for name in dirnames:
            rel = name if rel_dir == "." else rel_dir + "/" + name
            found[rel] = ("dir", None)
        for name in filenames:
            path = current / name
            rel = name if rel_dir == "." else rel_dir + "/" + name
            if path.is_symlink():
                found[rel] = ("link", os.readlink(path))
            elif path.is_file():
                found[rel] = ("file", path.read_bytes())
            else:
                found[rel] = ("other", None)
    return found


def _sample_box(folder):
    box = folder / "Box"
    (box / "nested" / "empty").mkdir(parents=True)
    (box / "nested" / "café.txt").write_text("héllo\n", encoding="utf-8")
    (box / "data.bin").write_bytes(bytes(range(256)))
    (box / ".hidden").write_text("dot\n", encoding="utf-8")
    (box / "note.txt").write_text("Hello\n", encoding="utf-8")
    return box


def _package_bytes(raw, key="", passes=1, legacy=False, folds=None):
    """A folder package around zip bytes, using the same geometry as the CLI."""
    digest = hashlib.sha256(raw).hexdigest()
    if legacy:
        folded = tesseract_fold.scramble(raw, key, folds)
        line = (
            f"TESSERACT-FOLD-FOLDER/1 key={int(bool(key))} geometry=legacy "
            f"sha256={digest} bytes={len(raw)}"
        )
        if folds is not None:
            line += " folds=" + tesseract_fold.fold_spec(folds)
    else:
        folded = tesseract_fold.scramble_multiscale(raw, key, passes)
        line = (
            f"TESSERACT-FOLD-FOLDER/1 key={int(bool(key))} geometry=multiscale "
            f"passes={passes} sha256={digest} bytes={len(raw)}"
        )
    return (line + "\n").encode("ascii") + folded


class FolderTest(unittest.TestCase):
    def test_folder_round_trip_keeps_the_tree_and_the_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            box = _sample_box(folder)
            before = _snapshot(box)
            package = folder / "packed.tess"
            code, out, err = run(
                ["--folder", str(box), "--key", "paper", "--output", str(package)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(out, b"")
            self.assertIn(f"wrote {package}", err)
            self.assertEqual(_snapshot(box), before)
            header = package.read_bytes().split(b"\n", 1)[0]
            self.assertTrue(header.startswith(b"TESSERACT-FOLD-FOLDER/1 key=1 "))
            self.assertIn(b"geometry=multiscale passes=1 ", header)
            self.assertNotIn(b"paper", header)
            restored = folder / "Restored"
            code, out, err = run(
                ["--decrypt", "--key", "paper", str(package), "--output", str(restored)]
            )
            self.assertEqual(code, 0, err)
            self.assertIn(f"restored {restored}", err)
            self.assertEqual(_snapshot(restored), before)
            self.assertEqual(_snapshot(box), before)
            empty = folder / "Empty"
            empty.mkdir()
            code, out, err = run(["--file", str(empty)])
            self.assertEqual(code, 0, err)
            code, out, err = run(
                ["--decrypt", str(folder / "Empty.tess"), "--output", str(folder / "Empty2")]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(list((folder / "Empty2").iterdir()), [])

    def test_folder_rejects_links_special_files_and_unsafe_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            box = _sample_box(folder)
            (box / "link").symlink_to(box / "note.txt")
            package = folder / "Box.tess"
            code, out, err = run([str(box)])
            self.assertEqual(code, 1)
            self.assertIn("symbolic link", err)
            self.assertFalse(package.exists())
            self.assertTrue((box / "note.txt").is_file())
            (box / "link").unlink()
            os.mkfifo(box / "pipe")
            code, out, err = run(["--folder", str(box), "--output", str(package)])
            self.assertEqual(code, 1)
            self.assertIn("special file", err)
            self.assertFalse(package.exists())
            (box / "pipe").unlink()
            code, out, err = run(
                ["--folder", str(box), "--output", str(box / "inside.tess")]
            )
            self.assertEqual(code, 1)
            self.assertIn("outside", err)
            self.assertFalse((box / "inside.tess").exists())
            code, out, err = run(
                ["--folder", str(box), "--output", str(folder), "--force"]
            )
            self.assertEqual(code, 1)
            self.assertIn("refusing to replace the directory", err)
            code, out, err = run(["--folder", str(box)])
            self.assertEqual(code, 0, err)
            code, out, err = run(["--folder", str(box)])
            self.assertEqual(code, 1)
            self.assertIn("already exists; pass --output to replace it", err)
            old = package.read_bytes()
            code, out, err = run(["--folder", str(box), "--output", str(package)])
            self.assertEqual(code, 1)
            self.assertIn("--force", err)
            self.assertEqual(package.read_bytes(), old)
            occupied = folder / "Taken"
            occupied.mkdir()
            (occupied / "keep.txt").write_text("stay", encoding="utf-8")
            code, out, err = run(
                ["--decrypt", "--force", str(package), "--output", str(occupied)]
            )
            self.assertEqual(code, 1)
            self.assertIn("new folder", err)
            self.assertEqual((occupied / "keep.txt").read_text(encoding="utf-8"), "stay")
            code, out, err = run(["--decrypt", str(package)])
            self.assertEqual(code, 1)
            self.assertIn("new folder", err)
            self.assertEqual((box / "note.txt").read_text(encoding="utf-8"), "Hello\n")

    def test_folder_header_selects_passes_legacy_and_folds(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            box = _sample_box(folder)
            package = folder / "passes.tess"
            code, out, err = run(
                [
                    "--folder",
                    str(box),
                    "--key",
                    "paper",
                    "--passes",
                    "2",
                    "--output",
                    str(package),
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn(b"passes=2", package.read_bytes().split(b"\n", 1)[0])
            self.assertNotIn(b"paper", package.read_bytes())
            restored = folder / "from-passes"
            code, out, err = run(
                ["--decrypt", "--key", "paper", str(package), "--output", str(restored)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(_snapshot(restored), _snapshot(box))
            wrong = folder / "wrong-passes"
            code, out, err = run(
                [
                    "--decrypt",
                    "--key",
                    "paper",
                    "--passes",
                    "1",
                    str(package),
                    "--output",
                    str(wrong),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("records 2 passes", err)
            self.assertFalse(wrong.exists())
            code, out, err = run(
                [
                    "--decrypt",
                    "--legacy",
                    "--key",
                    "paper",
                    str(package),
                    "--output",
                    str(folder / "no-legacy"),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("omit --legacy", err)
            self.assertFalse((folder / "no-legacy").exists())
            legacy = folder / "legacy.tess"
            code, out, err = run(
                ["--legacy", "--key", "paper", "--folder", str(box), "--output", str(legacy)]
            )
            self.assertEqual(code, 0, err)
            header = legacy.read_bytes().split(b"\n", 1)[0]
            self.assertIn(b"geometry=legacy", header)
            self.assertNotIn(b"passes=", header)
            back = folder / "from-legacy"
            code, out, err = run(
                ["--decrypt", "--key", "paper", str(legacy), "--output", str(back)]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(_snapshot(back), _snapshot(box))
            folded = folder / "folds.tess"
            code, out, err = run(
                ["--folds", "mx", "--folder", str(box), "--output", str(folded)]
            )
            self.assertEqual(code, 0, err)
            self.assertIn(b"folds=mx", folded.read_bytes().split(b"\n", 1)[0])
            unfolded = folder / "from-folds"
            code, out, err = run(["--decrypt", str(folded), "--output", str(unfolded)])
            self.assertEqual(code, 0, err)
            self.assertEqual(_snapshot(unfolded), _snapshot(box))
            mismatch = folder / "bad-folds"
            code, out, err = run(
                ["--decrypt", "--folds", "my", str(folded), "--output", str(mismatch)]
            )
            self.assertEqual(code, 1)
            self.assertIn("records folds", err)
            self.assertFalse(mismatch.exists())

    def test_wrong_key_and_a_damaged_header_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            box = _sample_box(folder)
            package = folder / "keyed.tess"
            code, out, err = run(
                ["--folder", str(box), "--key", "paper", "--output", str(package)]
            )
            self.assertEqual(code, 0, err)
            missed = folder / "missed"
            code, out, err = run(
                ["--decrypt", "--key", "other", str(package), "--output", str(missed)]
            )
            self.assertEqual(code, 1)
            self.assertIn("digest", err)
            self.assertFalse(missed.exists())
            code, out, err = run(
                ["--decrypt", str(package), "--output", str(folder / "nokey")]
            )
            self.assertEqual(code, 1)
            self.assertIn("used a key", err)
            self.assertFalse((folder / "nokey").exists())
            code, out, err = run(["--folder", str(package)])
            self.assertEqual(code, 1)
            self.assertIn("not a folder", err)
            code, out, err = run(["--decrypt", "--folder", str(box)])
            self.assertEqual(code, 1)
            self.assertIn("not a folder package", err)
            code, out, err = run(["--decrypt", str(box)])
            self.assertEqual(code, 1)
            self.assertIn("not a folder package", err)
            code, out, err = run(["--decrypt", "--file", str(box)])
            self.assertEqual(code, 1)
            self.assertIn("not a folder package", err)
            code, out, err = run([str(box), "and some words"])
            self.assertEqual(code, 0, err)
            self.assertFalse((folder / "Box.tess").exists())
            broken = folder / "broken.tess"
            broken.write_bytes(b"TESSERACT-FOLD-FOLDER/1 this is not a header\n")
            code, out, err = run(
                ["--decrypt", str(broken), "--output", str(folder / "nope")]
            )
            self.assertEqual(code, 1)
            self.assertIn("damaged folder header", err)
            self.assertFalse((folder / "nope").exists())
            raw_out = folder / "raw.bin"
            code, out, err = run(
                ["--decrypt", "--raw", "--binary", str(package), "--output", str(raw_out)]
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(raw_out.is_file())
            self.assertNotIn("restored", err)

    def test_folder_archive_rejects_slip_and_inflation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("Box/", b"")
                archive.writestr("Box/../../outside.txt", b"nope")
            package = folder / "slip.tess"
            package.write_bytes(_package_bytes(buf.getvalue()))
            code, out, err = run(
                ["--decrypt", str(package), "--output", str(folder / "Restored")]
            )
            self.assertEqual(code, 1)
            self.assertIn("unsafe path", err)
            self.assertFalse((folder / "Restored").exists())
            self.assertFalse((folder / "outside.txt").exists())
            deflated = io.BytesIO()
            with zipfile.ZipFile(deflated, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("Box/", b"")
                archive.writestr("Box/a.txt", b"hello hello hello")
            packed = folder / "deflated.tess"
            packed.write_bytes(_package_bytes(deflated.getvalue()))
            code, out, err = run(
                ["--decrypt", str(packed), "--output", str(folder / "Inflated")]
            )
            self.assertEqual(code, 1)
            self.assertIn("stored", err)
            self.assertFalse((folder / "Inflated").exists())
            honest = io.BytesIO()
            with zipfile.ZipFile(honest, "w", compression=zipfile.ZIP_STORED) as archive:
                info = zipfile.ZipInfo("Box/")
                info.external_attr = (stat.S_IFDIR | 0o755) << 16
                archive.writestr(info, b"")
                archive.writestr("Box/a.txt", b"hi")
            raw = honest.getvalue()
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                member = archive.getinfo("Box/a.txt")
                member.file_size = len(raw) + 1
                with self.assertRaises(ValueError) as raised:
                    tesseract_fold._safe_folder_zip_members(archive, len(raw))
                self.assertIn("larger than the zip", str(raised.exception))
                member.file_size = 2
                member.flag_bits |= 0x1
                with self.assertRaises(ValueError) as raised:
                    tesseract_fold._safe_folder_zip_members(archive, len(raw))
                self.assertIn("encrypted", str(raised.exception))
                member.flag_bits &= ~0x1
                member.external_attr = stat.S_IFLNK << 16
                with self.assertRaises(ValueError) as raised:
                    tesseract_fold._safe_folder_zip_members(archive, len(raw))
                self.assertIn("symbolic link", str(raised.exception))

    def test_menu_folds_and_unfolds_a_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            box = folder / "Box"
            box.mkdir()
            (box / "note.txt").write_text("Hello\n", encoding="utf-8")
            package = folder / "Box.tess"
            restored = folder / "Back"
            code, out, err = run(
                ["--menu"],
                ScriptedIn(
                    [
                        "10\n",
                        str(box) + "\n",
                        "paper\n",
                        "\n",
                        "\n",
                        "11\n",
                        str(package) + "\n",
                        "paper\n",
                        str(restored) + "\n",
                        "0\n",
                    ]
                ),
            )
            self.assertEqual(code, 0, err)
            self.assertIn(b"Fold a folder", out)
            self.assertIn(b"Unfold a folder", out)
            self.assertIn(b"Wrote ", out)
            self.assertIn(b"Restored folder: ", out)
            self.assertEqual((restored / "note.txt").read_text(encoding="utf-8"), "Hello\n")
            self.assertEqual((box / "note.txt").read_text(encoding="utf-8"), "Hello\n")
            self.assertTrue(package.is_file())
        code, out, err = run(["--menu"], ScriptedIn(["12\n", "0\n"]))
        self.assertEqual(code, 0, err)
        self.assertIn(b"Choose 0 through 11.", out)

    def test_folder_flag_combinations_exit_2(self):
        for argv in (
            ["--folder"],
            ["--check", "--folder", "Box"],
            ["--folder", "Box", "--map"],
            ["--folder", "Box", "--analyze"],
            ["--menu", "--folder", "Box"],
        ):
            code, out, err = run(argv)
            self.assertEqual(code, 2, argv)
            self.assertEqual(out, b"", argv)
            self.assertIn("usage:", err, argv)


if __name__ == "__main__":
    unittest.main()
