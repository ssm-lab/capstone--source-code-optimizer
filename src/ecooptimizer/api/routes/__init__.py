from ecooptimizer.api.routes.refactor_smell import router as RefactorRouter
from ecooptimizer.api.routes.detect_smells import router as DetectRouter
from ecooptimizer.api.routes.show_logs import router as LogRouter

__all__ = ["DetectRouter", "LogRouter", "RefactorRouter"]
