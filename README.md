# Transcribe a flashcard’s audio in Anki Desktop

Select a note with an English recording, review the transcript and save it in an empty field. For example, a language learner can fill the back of a listening card while keeping the original audio on the front. Fourier runs on your CPU. After the initial model download, audio stays on your computer.

[Download the Anki add-on](https://huggingface.co/oruk/oruk-fourier-2b/resolve/main/examples/anki/Fourier-English-Notes.ankiaddon?download=true) · [Anki Desktop](https://apps.ankiweb.net/) · [Model files](https://huggingface.co/oruk/oruk-fourier-2b/tree/3fda023e157ce7986f137f76fcf326ed6e08fa73/onnx/sherpa-int8)

## Install once

1. In Anki Desktop, choose **Tools → Add-ons → Install from file** and select `Fourier-English-Notes.ankiaddon`. Restart Anki.
2. Install Python 3.11 and FFmpeg if needed. In **Tools → Add-ons**, select **Fourier · Local English audio transcript** and click **View Files**. Open a terminal in that add-on folder, which contains `manifest.json` and `recognize.py`.
3. On macOS or Linux, run:

   ```sh
   mkdir -p user_files
   python3.11 -m venv user_files/venv
   user_files/venv/bin/python -m pip install 'sherpa-onnx==2.0.2' 'numpy==2.2.6' huggingface_hub
   user_files/venv/bin/hf download oruk/oruk-fourier-2b \
     --revision 3fda023e157ce7986f137f76fcf326ed6e08fa73 \
     --include 'onnx/sherpa-int8/*' --include config.json --local-dir user_files/model
   ```

   The ten `onnx/sherpa-int8/` model files plus repo-root `config.json` take 2.41 GB on disk (including `config.json` preserves model metadata and standard Hugging Face download accounting). Keep the `.onnx.data` files beside their `.onnx` files. If you already have this exact model, start Anki with `FOURIER_MODEL_DIR` set to its `sherpa-int8` folder to reuse it. To use an existing compatible Python runtime, set `FOURIER_PYTHON` to that interpreter’s absolute path.

If Anki cannot find FFmpeg on macOS, quit Anki and launch from a terminal where `ffmpeg -version` works:

```sh
FOURIER_FFMPEG="$(command -v ffmpeg)" /Applications/Anki.app/Contents/MacOS/anki
```

## Transcribe a note

1. Open **Browse** and select one note. It needs one field with a single local audio attachment such as `[sound:clip.mp3]`, plus a separate empty field for its transcript. Each clip can be up to 30 seconds and 64 MiB.
2. Choose **Notes → Transcribe English audio with Fourier…**. Pick the audio field and the empty destination field.
3. Review or edit the transcript. Click **OK** to save or **Cancel** to leave the note alone. **Edit → Undo** removes the saved transcript. Your audio, tags and scheduling stay in place.

A change to the selected source, destination or audio during recognition stops the save. Use recordings you own or have permission to process. Fourier’s weights are **CC BY-NC 4.0**. The Python add-on and optional provider are **AGPL-3.0-or-later**. The add-on archive includes the complete Python source and its license; the model is a separate download. [Model license](https://huggingface.co/oruk/oruk-fourier-2b#license) · [GNU AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html)

## Already using Speech Recognition for Anki?

The optional provider lets users of [abdnh’s Speech Recognition for Anki 1.1.1](https://github.com/abdnh/anki-asr/releases/tag/1.1.1) choose Fourier in that add-on’s provider list. Install the Fourier package directly from this page and complete its runtime setup first. To preview each result and protect filled fields, use the single-note command above. The other add-on’s bulk command writes directly to its selected destination.

1. Download [fourier_provider.py](https://huggingface.co/oruk/oruk-fourier-2b/resolve/main/examples/anki/fourier_provider.py?download=true). From **Tools → Add-ons**, select **Speech Recognition for Anki → View Files**. Create `user_files/providers/` there if missing, then place `fourier_provider.py` inside it.
2. In that same folder, create `__init__.py` containing `PROVIDERS = []` if it does not exist. Keep any existing providers, then append the following two lines **once**:

   ```python
   from .fourier_provider import Fourier
   PROVIDERS.append(Fourier)
   ```

3. Restart Anki. From **Browse → Notes → Transcribe Selected**, choose **Fourier**, then **English (local, noncommercial)**. This bridge uses the add-on’s own result cache and requires the Fourier package’s direct-install name, `oruk_fourier_notes`. [Upstream custom provider documentation](https://github.com/abdnh/anki-asr/tree/42ba7514f4b2e8df6f597dab9d5ec730bb0494cc#custom-providers)

## What was tested

Anki Desktop 26.09.4 on macOS installed the packaged release and exercised its Notes command, editable preview, save and Undo in a temporary collection with fixed recognizer output. The optional provider also loaded in the upstream 1.1.1 registry and returned its cached result. Separately, on a Linux CPU, the actual Fourier weights correctly transcribed all 22 words of a public JFK clip in a real Anki collection. The test preserved the source, another note, scheduling, and an unrelated change made during transcription. That one short clip verifies the workflow. [Verification receipt](./verification.json) · [Test audio](https://github.com/ggml-org/whisper.cpp/blob/b0a11594aec50892a02cd8d129eee2dfe93a8bb8/samples/jfk.wav)

## Build the add-on

Run `python3 build.py` from the repository root. It packages the Python sources in `addon/` and their AGPL license into `Fourier-English-Notes.ankiaddon`. The release can be installed through Anki Desktop’s **Install from file** command.
