# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Oruk, Inc.
"""Offline inference in a separate Python environment from Anki Desktop."""
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import sherpa_onnx


def recognize(path):
    model = Path(os.environ["FOURIER_MODEL_DIR"])
    required = ["conv_frontend.onnx", "encoder.int8.onnx", "encoder.int8.onnx.data",
                "decoder.int8.onnx", "decoder.int8.onnx.data", "tokenizer/tokenizer.json"]
    if any(not (model / f).is_file() for f in required):
        raise ValueError("Download the complete Fourier sherpa-int8 model folder first.")
    run = subprocess.run([os.environ.get("FOURIER_FFMPEG", "ffmpeg"), "-nostdin", "-v", "error",
                          "-protocol_whitelist", "file,pipe",
                          "-format_whitelist", "wav,mp3,mov,aac,ogg,flac,aiff,matroska,webm",
                          "-i", str(path.resolve()), "-map", "0:a:0", "-vn", "-sn", "-dn",
                          "-t", "30.25", "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"],
                         capture_output=True, timeout=45)
    if run.returncode:
        raise ValueError("FFmpeg could not decode the note’s audio attachment.")
    samples = np.frombuffer(run.stdout, dtype="<f4")
    if len(samples) > 30 * 16000:
        raise ValueError("This workflow accepts audio up to 30 seconds. Split the clip first.")
    if not samples.size:
        raise ValueError("No audio samples in the attachment.")
    rec = sherpa_onnx.OfflineRecognizer.from_qwen3_asr(
        conv_frontend=str(model / "conv_frontend.onnx"), encoder=str(model / "encoder.int8.onnx"),
        decoder=str(model / "decoder.int8.onnx"), tokenizer=str(model / "tokenizer"),
        num_threads=min(4, os.cpu_count() or 1), provider="cpu",
    )
    stream = rec.create_stream()
    stream.accept_waveform(16000, samples)
    rec.decode_stream(stream)
    return " ".join(stream.result.text.split())


if __name__ == "__main__":
    try:
        print(recognize(Path(sys.argv[1])))
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
