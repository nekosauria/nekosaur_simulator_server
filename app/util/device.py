import torch
from typing import  Any

def get_gpu_device() -> Any:
    """
    針對 Linux 環境優化的四大平台硬體偵測
    優先序: NVIDIA/AMD (cuda) -> Intel Arc (xpu) -> Mac (mps) -> CPU
    """
    # 檢查 NVIDIA GPU 或 AMD GPU (Linux 下 ROCm 也是對應 cuda)
    if torch.cuda.is_available():
        # 可以透過裝置名稱進一步區分是英偉達還是超微（純日誌紀錄用）
        device_name = torch.cuda.get_device_name(0).lower()
        if "amd" in device_name or "radeon" in device_name:
            print(f"Detected AMD GPU (ROCm) -> [{torch.cuda.get_device_name(0)}] -> Using 'cuda'")
        else:
            print(f"Detected NVIDIA GPU (CUDA) -> [{torch.cuda.get_device_name(0)}] -> Using 'cuda'")
        return "cuda"

    # 檢查 Intel Arc / Intel 顯示卡
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        print("Detected Intel GPU (Arc/Flex) -> Using 'xpu'")
        return torch.device("xpu")

    # 檢查 Mac / Apple Silicon 後端 (保留彈性)
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("Detected Apple Silicon 後端 -> Using 'mps'")
        return "mps"

    # Fallback 回 CPU
    print("No GPU acceleration detected -> Falling back to 'cpu'")
    return "cpu"