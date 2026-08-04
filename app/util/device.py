import gc
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


def get_gpu_dtype() -> torch.dtype:
    """自動偵測當前裝置支援的最佳數據精度 (dtype)。

    支援硬體：
    - NVIDIA GPU (CUDA): Ampere 架構以上優先使用 bfloat16，舊卡使用 float16
    - AMD GPU (ROCm): 最新 ROCm 支援 bfloat16，預設自動判斷
    - Apple Silicon GPU (MPS): 優先使用 float16（MPS 專屬最佳化）
    - Intel Arc / Data Center (XPU): 優先使用 bfloat16
    - CPU (Fallback): 預設使用 float32，防範運算溢位或不支援
    """
    try:
        device = get_gpu_device()
        # 如果回傳的是 torch.device 物件，統一轉成字串小寫處理
        device_str = str(device).lower()

        # 1. NVIDIA / AMD GPU (cuda)
        if "cuda" in device_str:
            # 檢查 CUDA 驅動與顯卡是否支援 bfloat16 (RTX 30 系列以上 / A100 / H100 等)
            if hasattr(torch.cuda, "is_bf16_supported") and torch.cuda.is_bf16_supported():
                logger.debug("CUDA supports bfloat16 -> Using 'torch.bfloat16'")
                return torch.bfloat16
            else:
                logger.debug("CUDA does not support bfloat16 -> Falling back to 'torch.float16'")
                return torch.float16

        # 2. Intel GPU (xpu)
        elif "xpu" in device_str:
            if hasattr(torch.xpu, "is_bf16_supported") and torch.xpu.is_bf16_supported():
                logger.debug("XPU supports bfloat16 -> Using 'torch.bfloat16'")
                return torch.bfloat16
            else:
                logger.info("XPU using 'torch.float16'")
                return torch.float16

        # 3. Apple Silicon (mps)
        elif "mps" in device_str:
            # Apple Silicon 的 Metal 引擎針對 float16 做了極致優化（不建議在 MPS 使用 bfloat16）
            logger.debug("MPS detected -> Using 'torch.float16'")
            return torch.float16

        # 4. CPU (cpu) 或其他例外
        else:
            logger.debug("CPU detected -> Using 'torch.float32' for safety")
            return torch.float32

    except Exception as e:
        logger.error(
            f"Error occurred during GPU dtype detection: {e}. Defaulting to 'torch.float32'",
            exc_info=True,
        )
        return torch.float32



def empty_device_cache(device: str) -> None:
    """
    釋放指定裝置上，PyTorch 快取分配器持有但目前未使用的記憶體。

    注意：
    - 不會回收仍被引用中的 tensor（不是萬能的記憶體洩漏解法）
    - 頻繁呼叫會有額外的重新分配開銷，建議只在「切換模型」或
      「批次處理之間」呼叫，不要每次 forward 都清
    """
    device = (device or "").lower()

    if device == "cuda":
        if not torch.cuda.is_available():
            logger.warning("empty_device_cache: device='cuda' 但 CUDA 不可用，略過")
            return
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()  # 順手清理跨 process 共享的 CUDA IPC 記憶體控制代碼
        logger.debug("CUDA cache cleared")

    elif device == "mps":
        if not torch.backends.mps.is_available():
            logger.warning("empty_device_cache: device='mps' 但 MPS 不可用，略過")
            return
        torch.mps.empty_cache()
        logger.debug("MPS cache cleared")

    elif device == "xpu":
        # Intel GPU（部分 PyTorch 版本支援）
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            torch.xpu.empty_cache()
            logger.debug("XPU cache cleared")
        else:
            logger.warning("empty_device_cache: device='xpu' 但不可用，略過")

    elif device == "cpu":
        # CPU 沒有「顯存快取」這回事，頂多手動觸發一次 Python GC
        gc.collect()
        logger.debug("CPU: triggered gc.collect()")

    else:
        logger.warning(f"empty_device_cache: 未知的 device='{device}'，略過")