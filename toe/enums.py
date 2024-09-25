from enum import Enum


class ElementStatus(Enum):
    UNDEFINED   = 0
    ACTIVE      = 1
    DAMAGED     = 2
    DESTROYED   = 3