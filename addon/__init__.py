# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Oruk, Inc.
"""Anki Browser → Notes → Transcribe English audio with Fourier…"""
from aqt import gui_hooks
from aqt.operations import CollectionOp, QueryOp
from aqt.qt import QAction, QInputDialog
from aqt.utils import showWarning, tooltip

from .core import capture, choices, prepare, save


def run(browser):
    ids = browser.selected_notes()
    if len(ids) != 1:
        return showWarning("Select one note in Browse.", parent=browser)
    nid = ids[0]
    col = browser.mw.col
    note = col.get_note(nid)
    sources, blanks = choices(note)
    if not sources or not blanks:
        return showWarning("The note needs one field containing a local audio attachment and a separate empty field.", parent=browser)
    title = "Fourier · English transcript"
    source, ok = QInputDialog.getItem(browser, title,
        "Local noncommercial use (CC BY-NC 4.0). Audio field:", sources, 0, False)
    if not ok:
        return
    target, ok = QInputDialog.getItem(browser, title, "Write the transcript to this empty field:", blanks, 0, False)
    if not ok:
        return
    try:
        plan = prepare(col, nid, source, target)
    except ValueError as error:
        return showWarning(str(error), parent=browser)

    def fail(error):
        showWarning(str(error), parent=browser)

    def review(result):
        if browser.mw.col is not col or list(browser.selected_notes()) != [nid]:
            return fail("The selected note changed. Nothing was saved.")
        checksum, text = result
        reviewed, accepted = QInputDialog.getMultiLineText(browser, title,
            f"{plan.file.name} → {target} (note {nid}). Edit the transcript, then choose OK to save:",
            text)
        if not accepted:
            return

        def write(current):
            if current is not col:
                raise ValueError("The collection changed. Nothing was saved.")
            return save(current, plan, checksum, reviewed)

        def after_edits():
            CollectionOp(parent=browser, op=write).failure(fail).success(
                lambda _: tooltip("Transcript saved. Edit → Undo restores the field.", parent=browser)
            ).run_in_background()
        browser.editor.call_after_note_saved(after_edits)

    QueryOp(parent=browser, op=lambda _: capture(plan), success=review).failure(fail).without_collection().with_progress(
        label="Transcribing English audio on this computer…"
    ).run_in_background()


def add_action(browser):
    action = QAction("Transcribe English audio with Fourier…", browser)
    action.triggered.connect(lambda _checked=False: browser.editor.call_after_note_saved(lambda: run(browser)))
    browser.form.menu_Notes.addAction(action)


gui_hooks.browser_menus_did_init.append(add_action)
