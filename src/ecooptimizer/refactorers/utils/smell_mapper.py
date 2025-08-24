import hashlib
import logging
from pathlib import Path
from difflib import SequenceMatcher
import tempfile
from typing import Literal

from ecooptimizer.data_types.api import ChangedFile
from ecooptimizer.data_types.smell import Smell
from ecooptimizer.utils.load_smells import load_smells_from_file
from ecooptimizer.utils.output_manager import save_json_files

logger = logging.getLogger("refactor")


def _get_file_lines(file: Path):
    logger.debug(f"Reading file: {file}")
    text = file.read_text(encoding="utf-8")

    return text.splitlines(keepends=True)


def _shift_smells(
    smell: dict,
    subscripts: list[str | int],
    opcodes: tuple[Literal["replace", "delete", "insert", "equal"], int, int, int, int],
    lines: tuple[list[str], list[str]],
):
    """
    Navigate into a nested dict/list structure and apply a shift to the target int value.

    Args:
        smell (dict): smell dictionary.
        subscripts (list): list of keys/indices to reach the target value.
        opcodes: single opcode tuple from SequenceMatcher.get_opcodes()
        lines (tuple[list[str], list[str]]): tuple containing the original and modified lines of the module
    """
    target = smell
    for key in subscripts[:-1]:
        target = target[key]

    last_key = subscripts[-1]

    if not target[last_key]:
        return

    dirty = False
    removed = False

    logger.debug(f"Opcodes: {opcodes}")
    logger.debug(f"Target: {target}, last key: {last_key}")

    tag, i1, i2, j1, j2 = opcodes

    # --- Case 1: edits before smell -> line shift ---
    if tag in ("insert", "delete", "replace") and i2 <= target[last_key]:
        line_shift = (j2 - j1) - (i2 - i1)
        logger.debug(f"Line shift detected: {line_shift} (before smell lines)")
        target[last_key] += line_shift
        if subscripts[0] == "occurences":
            target["endLine"] += line_shift

    # --- Case 2: deletion or replacement directly affecting smell lines ---
    elif tag in ("delete", "replace"):
        # Handle single-line smells
        if i1 <= target[last_key] < i2:
            logger.debug(
                f"Smell line {target[last_key]} affected by {tag} opcode ({i1}, {i2}). Marking smell as removed."
            )
            removed = True

        # Handle multi-line smells (startLine -> endLine)
        elif subscripts[0] == "occurences":
            start_line = target.get("startLine", target[last_key])
            end_line = target.get("endLine", target[last_key])

            # Fully replaced/deleted
            if i1 <= start_line and end_line < i2:
                logger.debug(
                    f"Smell lines {start_line}-{end_line} fully affected by {tag} opcode ({i1}, {i2}). Marking smell as removed."
                )
                removed = True

            # Partial overlap → dirty
            elif (i1 <= start_line < i2 <= end_line) or (start_line < i1 < end_line <= i2):
                logger.debug(
                    f"Smell lines {start_line}-{end_line} partially affected by {tag} opcode ({i1}, {i2}). Marking smell as dirty."
                )
                dirty = True

    # --- Case 3: change overlaps smell lines ---
    elif subscripts[0] == "occurences" and i1 < target[last_key] and i2 > target[last_key]:
        logger.debug("Change overlaps smell lines. Running column-level diff.")
        # Narrow diff check on overlapping lines
        orig_overlap = "".join(lines[0][i1:i2])
        mod_overlap = "".join(lines[1][j1:j2])

        # Run column-level diff
        col_sm = SequenceMatcher(None, orig_overlap, mod_overlap)
        for ctag, ci1, ci2, cj1, cj2 in col_sm.get_opcodes():
            logger.debug(f"Col opcode: ctag={ctag}, ci1={ci1}, ci2={ci2}, cj1={cj1}, cj2={cj2}")
            if ctag in ("insert", "delete", "replace"):
                # if edit is before smell column
                if ci2 <= target[last_key]:
                    col_shift = (cj2 - cj1) - (ci2 - ci1)
                    logger.debug(f"Column shift detected: {col_shift} (before smell columns)")
                    target["column"] += col_shift
                    target["endColumn"] += col_shift
                # if edit intersects smell columns
                elif ci1 < target[last_key] and ci2 > target[last_key]:
                    logger.debug("Edit intersects smell columns. Marking as dirty.")
                    dirty = True
                    break

    return smell, removed, dirty


def _adjust_smells_in_file(
    original_module_path: Path,
    temp_module_path: Path,
    module_path: Path,
    smell_id: str,
    analysis_path: Path,
):
    logger.debug(
        f"Starting adjust_smells_after_refactor for module_path={module_path}, "
        f"smell_id={smell_id}, analysis_path={analysis_path}"
    )
    """
    Update (line, column) ranges for smells after a refactor of a single file.

    Each smell dict must contain:
      - line (1-based)
      - column  (1-based, inclusive)
      - endLine   (1-based)
      - endColumn    (1-based, exclusive)   <-- recommend exclusive to avoid off-by-one
    You can change key names via parameters above.

    Strategy:
      1) Compute line-level shifts with SequenceMatcher -> fast line mapping.
      2) For smells:
         - Map start/end lines by adding the precomputed line offset.
         - If single-line: compute char-level column shift. If edit overlaps,
           try to re-locate the exact original substring in the new line.
         - If multi-line: map boundary lines; if edits overlap the span OR the
           number of lines inside changed, attempt whole-snippet re-anchoring
           across the entire modified file. If that fails, mark as uncertain.

    Returns the updated smells list (in-place updated copies) with optional flags:
      - smell['occurences'][0]['occurences'][0][mark_uncertain_key] = True when we couldn't be 100% sure.
      - smell['occurences'][0]['occurences'][0][mark_deleted_key]   = True if the original snippet no longer exists.
    """

    logger.debug(f"Adjusting smells after refactor for module: {module_path}")
    logger.debug(f"Smell ID: {smell_id}")
    logger.debug(f"Original module path: {original_module_path}")
    logger.debug(f"Analysis path: {analysis_path}")

    logger.debug(f"Loading smells from original analysis file: {analysis_path}")
    smells = load_smells_from_file(analysis_path)

    mod_smells = dict(smells[str(original_module_path)]["smells"])
    if mod_smells.get(smell_id):
        mod_smells.pop(smell_id)

    orig_lines = _get_file_lines(temp_module_path)
    mod_lines = _get_file_lines(module_path)

    sm = SequenceMatcher(None, orig_lines, mod_lines)

    updated_smells = dict(smells)
    removed_smells = []
    dirty_smells = []

    removed = False
    dirty = False

    for smell in mod_smells.values():
        logger.debug(f"Processing smell id: {smell['id']}")

        subscripts: list[list[str | int]] = []
        if smell["additionalInfo"]["innerLoopLine"]:
            subscripts.append(["additionalInfo", "innerLoopLine"])
        for i in range(len(smell["occurences"])):
            subscripts.append(["occurences", i, "line"])

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            logger.debug(
                f"Opcode: tag={tag}, i1={i1}, i2={i2}, j1={j1}, j2={j2} for smell id: {smell['id']}"
            )
            for sub in subscripts:
                returned = _shift_smells(smell, sub, (tag, i1, i2, j1, j2), (orig_lines, mod_lines))

                if not returned:
                    continue

                smell, removed, dirty = returned

                if removed:
                    mod_smells.pop(smell["id"])
                    removed_smells.append(smell)
                    break
                elif dirty:
                    mod_smells.pop(smell["id"])
                    dirty_smells.append(smell)
                    break

        logger.debug(f"Updating smell id: {smell['id']} in updated_smells.")
        updated_smells[str(original_module_path)]["smells"] = mod_smells

    try:
        logger.debug(f"Removing temporary original module file: {temp_module_path}")
        temp_module_path.unlink()
    except Exception as e:
        logger.error("Had trouble removing the temp module file", exc_info=e)

    sremoved = "\n".join(
        [f"{smell['symbol']} at line {smell['occurences'][0]['line']}" for smell in removed_smells]
    )
    sdirty = "\n".join(
        [f"{smell['symbol']} at line {smell['occurences'][0]['line']}" for smell in dirty_smells]
    )

    if sremoved:
        # print(f"Removed smells:\n{sremoved}")
        logger.debug(f"Removed smells:\n{sremoved}")
    if sdirty:
        # print(f"Dirty smells:\n{sdirty}")
        logger.debug(f"Dirty smells:\n{sdirty}")

    return updated_smells, removed_smells, dirty_smells


def adjust_modified_files(
    modified_files: list[ChangedFile],
    proj_root: Path,
    analysis_file: Path,
    smell: Smell,
    temp: bool = False,
):
    removed_smells = []
    dirty_smells = []
    updated_smells = {}

    for cfile in modified_files:
        try:
            logger.debug(f"Adjusting smells in modified file: {cfile.original}")
            cfile_path = Path(cfile.original)
            root_idx = cfile_path.parts.index(proj_root.name)
            rel_path = Path(*cfile_path.parts[root_idx:])

            base_temp_dir = Path(tempfile.gettempdir()) / ".ecooptimizer" / str(smell.id)
            file_hash = hashlib.sha1(str(rel_path).encode()).hexdigest()
            temp_file_name = file_hash + cfile_path.suffix
            temp_module_path = base_temp_dir / temp_file_name

            updated_smells, removed_smells, dirty_smells = _adjust_smells_in_file(
                cfile_path,
                temp_module_path,
                Path(cfile.refactored),
                smell.id,
                analysis_file,
            )
        except Exception:
            logger.error("Unable to properly adjust smells in module.")
            updated_smells[cfile.original]["dirty"] = True

    updated_smells[smell.path]["smells"].pop(smell.id, None)

    updated_analysis_file = analysis_file
    if temp:
        if analysis_file.name == "energy_smells.temp.json":
            updated_analysis_file = analysis_file
        else:
            updated_analysis_file = analysis_file.parent / "energy_smells.temp.json"
    else:
        if analysis_file.name == "energy_smells.updated.json":
            updated_analysis_file = analysis_file
        else:
            updated_analysis_file = analysis_file.parent / "energy_smells.updated.json"

    logger.debug(f"Saving updated smells to {updated_analysis_file}")
    save_json_files(updated_analysis_file, updated_smells)

    if not removed_smells and not dirty_smells:
        logger.info(f"Refactoring completed successfully. Modified files: {modified_files}")
        print("Refactoring completed successfully.")

    else:
        if removed_smells:
            print(
                f"The following smells were removed due to refactoring of other smells: {removed_smells}"
            )
        if dirty_smells:
            print(
                f"The following smells might have been affected by refactoring of other smells: {removed_smells}"
            )

        print("Please re-analyse to see any remaining smells.")
