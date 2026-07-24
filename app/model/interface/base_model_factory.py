from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

# 抽出共用 get_model 方法,  並寫一個抽象方法規定子類別實作模型初始化(使用泛型)
class BaseModelFactory(ABC, Generic[T]):
    """全域模型工廠共用基底：管理單例模型的存取邏輯"""

    @classmethod
    @abstractmethod
    def init_models(cls, root_path: str) -> None:
        """在 Flask App 啟動時進行冷啟動加載，子類別必須實作"""
        raise NotImplementedError(f"{cls.__name__} 必須實作 init_models")

    @classmethod
    def get_model(cls, model_type: str) -> T:
        model = cls._instances.get(model_type)
        if model is None:
            raise ValueError(f"Unknown model type or model not initialized: {model_type}")
        return model