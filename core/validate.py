import json
import logging
from pathlib import Path

from attr import dataclass
from jsonschema import Draft202012Validator
from typing import Tuple, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    path: str
    line_no: int
    message: str


@dataclass
class ValidatedObject:
    origin: str
    data: Any


class Validator:
    def __init__(self, schema_path: str | Path, origin: str):
        self.origin = origin
        self.schema_path = Path(schema_path)

        with open(self.schema_path, "r", encoding="utf-8") as file:
            schema = json.load(file)

        self.validator = Draft202012Validator(schema)
        logger.debug(
            "Validator initialized with schema=%s origin=%s",
            self.schema_path,
            self.origin,
        )

    def get_validated_object(
        self, line: str, line_no: int
    ) -> Tuple[Optional[ValidatedObject], List[ValidationError]]:
        try:
            obj = json.loads(line)
            logger.debug("Validated object: %s", obj)
        except json.JSONDecodeError as e:
            return None, [ValidationError("", line_no, f"Invalid JSON: {e}")]

        errors: List[ValidationError] = []
        for error in self.validator.iter_errors(obj):
            logger.info("Validation error: %s", error.message)
            path = ".".join(str(p) for p in error.path)
            errors.append(ValidationError(path, line_no, error.message))

        if errors:
            return None, errors

        return ValidatedObject(origin=self.origin, data=obj), []

    def get_validated_objects_from_file(
        self, file_path: str | Path
    ) -> Tuple[List[ValidatedObject], List[ValidationError]]:
        all_errors: List[ValidationError] = []
        all_objects: List[ValidatedObject] = []

        with open(file_path, "r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                logger.debug("Processing line: %s", line)

                s = line.strip()

                if not s:
                    continue

                obj, errors = self.get_validated_object(s, line_no)
                if obj is None:
                    all_errors.extend(errors)
                    continue

                all_objects.append(obj)

        return all_objects, all_errors
