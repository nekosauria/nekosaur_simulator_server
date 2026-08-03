from typing import Any
import torch
from util.common import common

logger = common.logger


def get_gpu_device() -> Any:
    """針對 Linux 環境優化的四大平台硬體偵測

    優先序: NVIDIA/AMD (cuda) -> Intel Arc (xpu) -> Mac (mps) -> CPU 發生任何異常或未偵測到加速器時，預設回傳 'cpu'
    """
    try:
        # 1. 檢查 NVIDIA GPU 或 AMD GPU (Linux 下 ROCm 也是對應 cuda)
        if torch.cuda.is_available():
            try:
                device_name = torch.cuda.get_device_name(0).lower()
                if "amd" in device_name or "radeon" in device_name:
                    logger.info(
                        f"Detected AMD GPU (ROCm) -> [{torch.cuda.get_device_name(0)}] -> Using 'cuda'"
                    )
                else:
                    logger.info(
                        f"Detected NVIDIA GPU (CUDA) -> [{torch.cuda.get_device_name(0)}] -> Using 'cuda'"
                    )
            except Exception as name_err:
                # 即使取得裝置名稱失敗，只要 cuda.is_available() 是 True 仍可使用 cuda
                logger.warning(
                    f"CUDA is available, but failed to get device name: {name_err}"
                )

            return "cuda"

        # 2. 檢查 Intel Arc / Intel 顯示卡 (保持原樣回傳 torch.device("xpu"))
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            logger.info("Detected Intel GPU (Arc/Flex) -> Using 'xpu'")
            return torch.device("xpu")

        # 3. 檢查 Mac / Apple Silicon 後端 (MPS)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("Detected Apple Silicon 後端 -> Using 'mps'")
            return "mps"

        # 4. 未偵測到任何可用的硬體加速器
        logger.info("No GPU acceleration detected -> Falling back to 'cpu'")
        return "cpu"

    except Exception as e:
        # 捕捉任何驅動、PyTorch 內部或環境異常，確保程式不崩潰並保底回傳 'cpu'
        logger.error(
            f"Error occurred during GPU device detection: {e}. Defaulting to 'cpu'",
            exc_info=True,
        )
        return "cpu"