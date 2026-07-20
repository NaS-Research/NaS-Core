from enum import StrEnum


class DataClassification(StrEnum):
    PUBLIC_OPEN = "public_open"
    LICENSED = "licensed"
    CONTROLLED = "controlled"
    PHI = "phi"


_CLASSIFICATION_RANK = {
    DataClassification.PUBLIC_OPEN: 0,
    DataClassification.LICENSED: 1,
    DataClassification.CONTROLLED: 2,
    DataClassification.PHI: 3,
}


def most_restrictive(
    classifications: list[DataClassification],
) -> DataClassification:
    if not classifications:
        raise ValueError("At least one data classification is required")
    return max(classifications, key=_CLASSIFICATION_RANK.__getitem__)
