from pathlib import Path
import json
from typing import Dict, Any, List, Union

from backend.app.config import get_logger, settings

logger = get_logger(__name__)

BASE_STORAGE = Path(settings.STORAGE_DIR) if hasattr(settings, "STORAGE_DIR") else Path("storage")
JSON_DIR = BASE_STORAGE / "json_tasks"


def _get_next_task_index() -> int:
    """
    Find next task number based on existing files
    """
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    existing_files = list(JSON_DIR.glob("task_*.json"))

    if not existing_files:
        return 1

    numbers = []
    for f in existing_files:
        try:
            num = int(f.stem.split("_")[1])
            numbers.append(num)
        except:
            continue

    return max(numbers) + 1 if numbers else 1


def save_ocr_json(result: Union[Dict[str, Any], List[Any]], base_filename: str) -> List[str]:
    """
    Save OCR result into sequential task files:
    task_1.json, task_2.json, task_3.json ...
    """
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)

        saved_files = []

        # 🔢 get starting index
        current_index = _get_next_task_index()

        # 🔥 CASE 1: result is LIST
        if isinstance(result, list):
            for item in result:
                file_path = JSON_DIR / f"task_{current_index}.json"

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(item, f, indent=4, ensure_ascii=False)

                saved_files.append(str(file_path))
                current_index += 1

        # 🔥 CASE 2: single dict
        else:
            file_path = JSON_DIR / f"task_{current_index}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)

            saved_files.append(str(file_path))

        logger.info(
            "OCR JSON saved successfully",
            files=saved_files,
            total=len(saved_files)
        )

        return saved_files

    except Exception as e:
        logger.error(
            "Failed to save OCR JSON",
            filename=base_filename,
            error=str(e),
            exc_info=True
        )
        raise
