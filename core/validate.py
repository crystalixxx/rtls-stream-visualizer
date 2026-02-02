import json
import logging
from pathlib import Path

from attr import dataclass
from jsonschema import Draft202012Validator
from typing import Tuple, List, Any, Optional

from core.config import ValidationItem

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
    def __init__(self, validators: list[ValidationItem]):
        if not validators:
            raise ValueError("At least one validation schema is required")

        self.validators: List[Tuple[ValidationItem, Draft202012Validator]] = []

        for validator in validators:
            with open(validator.schema_path, "r", encoding="utf-8") as file:
                scheme = json.load(file)

                self.validators.append((validator, Draft202012Validator(scheme)))

        logger.debug("Validator initialized with validators: %s", self.validators)

    def get_validated_object(
        self, line: str, line_no: int
    ) -> Tuple[Optional[ValidatedObject], List[ValidationError]]:
        try:
            obj = json.loads(line)
            logger.debug("Validated object: %s", obj)
        except json.JSONDecodeError as e:
            return None, [ValidationError("", line_no, f"Invalid JSON: {e}")]

        matches: List[ValidationItem] = []
        errors_by_schema: List[List[ValidationError]] = []

        for item, validator in self.validators:
            errors: List[ValidationError] = []
            for error in validator.iter_errors(obj):
                logger.info("Validation error: %s", error.message)

                path = ".".join(str(p) for p in error.path)
                errors.append(ValidationError(path, line_no, error.message))

            errors_by_schema.append(errors)
            if not errors:
                matches.append(item)

        if len(matches) == 1:
            match = matches[0]
            return ValidatedObject(origin=match.origin, data=obj), []

        if len(matches) > 1:
            names = ", ".join(item.name for item in matches)
            return (
                None,
                [ValidationError("", line_no, f"Multiple schemas matched: {names}")],
            )

        if len(self.validators) == 1:
            return None, errors_by_schema[0]

        return None, [ValidationError("", line_no, "No matching schema")]

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
