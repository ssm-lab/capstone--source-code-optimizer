from .refactor_smell import router as RefactorRouter
from .detect_smells import router as DetectRouter
from .show_logs import router as LogRouter
from .refactor_by_type import router as RefactorByTypeRouter

__all__ = ["DetectRouter", "LogRouter", "RefactorRouter", "RefactorByTypeRouter"]
