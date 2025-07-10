from abc import ABC
from typing import Optional
import logging

from numpy import dtype, ndarray

from matching import MatchResult
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
from pathlib import Path

DEFAULT_PLOT_SAVE_PATH = Path.cwd() / "plots"


class ResultMethod(ABC):
    def __init__(self, match_results: list[MatchResult]) -> None:
        self.matches = match_results


class Roc(ResultMethod):
    def __init__(self, match_results: list[MatchResult], method_name: str) -> None:
        super().__init__(match_results)

        result = self.fpr_tpr_calc()
        if result is None:
            return None

        (fpr, tpr, thresholds) = result
        self.plot_roc(method_name, fpr, tpr, f"AUC{self.auc(fpr, tpr)}")

    def fpr_tpr_calc(self) -> Optional[tuple]:
        if not self.matches:
            logging.warning("Match result is empty. No roc plots will be made")
            return None

        y_true = [int(match.is_same_image) for match in self.matches]
        y_scores = [-match.hamming_distance for match in self.matches]

        fpr, tpr, thresholds = roc_curve(y_true, y_scores)

        return (fpr, tpr, thresholds)

    def auc(self, fpr, tpr) -> float:
        return auc(fpr, tpr)

    def plot_roc(self, method_name: str, x, y, desc: Optional[str] = None):
        plt.figure(figsize=(6, 6))
        plt.plot(x, y, color="blue", lw=2, label={desc})
        plt.plot([0, 1], [0, 1], linestyle="--", color="gray")

        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve with Thresholds")
        plt.legend(loc="lower right")
        plt.grid(True)
        plt.tight_layout()

        save_dir = DEFAULT_PLOT_SAVE_PATH / "roc"
        Path.mkdir(save_dir, parents=True, exist_ok=True)
        save_path = save_dir / f"{method_name}_roc.png"
        plt.savefig(save_path)
