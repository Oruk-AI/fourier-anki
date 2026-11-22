# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Oruk, Inc.
"""Optional user_files/providers provider for Speech Recognition for Anki 1.1.1."""
from pathlib import Path

from ...providers.provider import Provider, ProviderConfig
from oruk_fourier_notes.core import infer, media_file
from aqt import mw


class Fourier(Provider):
    name = "fourier"
    config_class = ProviderConfig

    def transcribe(self, filename, lang):
        if lang != "en":
            raise ValueError("Fourier recognizes English.")
        media = Path(mw.col.media.dir()).resolve()
        path = Path(filename)
        if not path.is_absolute():
            path = media / path
        if path.parent.resolve() != media:
            raise ValueError("Select an audio attachment from this collection.")
        # Validate before the host opens the file to check its transcript cache.
        return super().transcribe(str(media_file(media, path.name)), lang)

    def _transcribe(self, filename, lang):
        return infer(Path(filename))

    @classmethod
    def languages(cls):
        return [("en", "English (local, noncommercial)")]
