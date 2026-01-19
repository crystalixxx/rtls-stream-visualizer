import json
import logging

from attr import dataclass
from jsonschema import Draft202012Validator
from typing import Tuple, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    path: str
    line_no: int
    message: str


class Validator:
    def __init__(self, schema_path: str):
        with open(schema_path, 'r') as file:
            self.schema = json.load(file)

        self.validator = Draft202012Validator(self.schema)
        logger.debug("Validator initialized with schema: %s", schema_path)

    def _get_validated_object(self, line: str, line_no: int) -> Tuple[Optional[Any], List[ValidationError]]:
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

        return None if len(errors) > 0 else obj, errors

    def get_validated_objects_from_file(self, file_path: str) -> Tuple[List[Any], List[ValidationError]]:
        all_errors: List[ValidationError] = []
        all_objects: List[Any] = []

        with open(file_path, 'r', encoding='utf-8') as file:
            for line_no, line in enumerate(file, start=1):
                logger.debug("Processing line: %s", line)

                s = line.strip()

                if not s:
                    continue

                obj, errors = self._get_validated_object(s, line_no)
                if obj is None:
                    all_errors.extend(errors)
                    continue

                all_objects.append(obj)

        return all_objects, all_errors
