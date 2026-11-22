# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Oruk, Inc.
"""Read one note and save one reviewed transcript through Anki’s undoable API."""
from dataclasses import dataclass
import hashlib
import html
import os
from pathlib import Path
import re
import subprocess

SOUND = re.compile(r"\[sound:([^\]\r\n]+)\]")
FORMATS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".aif", ".aiff", ".webm"}


def media_file(media_dir, filename):
    if not filename or any(c in filename for c in "/\\:\x00") or Path(filename).suffix.lower() not in FORMATS:
        raise ValueError("Choose one audio file stored in this collection’s media folder.")
    directory = Path(media_dir).resolve()
    path = directory / filename
    if path.is_symlink() or not path.is_file() or path.resolve().parent != directory:
        raise ValueError("The audio file is missing or is outside the collection’s media folder.")
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Choose a short audio attachment under 64 MiB.")
    return path


def choices(note):
    return [k for k in note.keys() if len(SOUND.findall(note[k])) == 1], [k for k in note.keys() if not note[k].strip()]


@dataclass(frozen=True)
class Plan:
    note_id: int
    note_type: int
    source: str
    target: str
    original: str
    target_original: str
    file: Path


def prepare(col, nid, source, target):
    note = col.get_note(nid)
    sources, blanks = choices(note)
    if source not in sources or target not in blanks or source == target:
        raise ValueError("Choose a field with one audio attachment and a separate, empty destination field.")
    file = media_file(col.media.dir(), SOUND.findall(note[source])[0])
    return Plan(nid, note.mid, source, target, note[source], note[target], file)


def digest(path):
    with path.open("rb") as handle:
        h = hashlib.sha256()
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def infer(path):
    folder = Path(__file__).resolve().parent
    user_dir = folder / "user_files"
    default_python = user_dir / ("venv/Scripts/python.exe" if os.name == "nt" else "venv/bin/python")
    python = Path(os.environ.get("FOURIER_PYTHON", default_python))
    if not python.is_file():
        raise ValueError("Install the Fourier Python environment as described in the add-on guide.")
    env = os.environ.copy()
    # Embedded Anki can set a Python path that belongs to a different runtime.
    for key in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(key, None)
    env.setdefault("FOURIER_MODEL_DIR", str(user_dir / "model/onnx/sherpa-int8"))
    run = subprocess.run([str(python), str(folder / "recognize.py"), str(path)],
                         env=env, capture_output=True, text=True, timeout=120)
    if run.returncode:
        detail = run.stderr.strip().splitlines()
        raise ValueError(detail[-1] if detail else "Local transcription failed.")
    text = run.stdout.strip()
    if not text:
        raise ValueError("No speech was recognized. The note was left untouched.")
    return text


def capture(plan):
    checksum = digest(plan.file)
    return checksum, infer(plan.file)


def save(col, plan, checksum, transcript):
    if not transcript.strip():
        raise ValueError("The transcript is empty.")
    try:
        fresh = prepare(col, plan.note_id, plan.source, plan.target)
    except Exception as exc:
        raise ValueError("The note changed during transcription. Nothing was saved.") from exc
    if fresh != plan or digest(fresh.file) != checksum:
        raise ValueError("The note or the attached audio changed. Nothing was saved.")
    note = col.get_note(plan.note_id)
    note[plan.target] = "<br>".join(html.escape(line, quote=False) for line in transcript.strip().splitlines())
    entry = col.add_custom_undo_entry("Transcribe English audio with Fourier")
    col.update_note(note)
    return col.merge_undo_entries(entry)
