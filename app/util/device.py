import gc
import logging
import os
from typing import Any

import psutil
import torch

from util.common import common


logger = common.logger


def get_gpu_device() -> Any:
    """針對 Linux / macOS 環境進行硬體加速器偵測。

    優先序:
    NVIDIA / AMD (cuda)
        -> Intel Arc (xpu)
        -> Apple Silicon (mps)
        -> CPU

    發生任何異常或未偵測到加速器時，預設回傳 'cpu'。
    """
    try:
        # NVIDIA GPU / AMD GPU
        # Linux 下 ROCm 也是透過 torch.cuda API 使用
        if torch.cuda.is_available():
            try:
                device_name = torch.cuda.get_device_name(0).lower()

                if "amd" in device_name or "radeon" in device_name:
                    logger.info(
                        f"Detected AMD GPU (ROCm) -> "
                        f"[{torch.cuda.get_device_name(0)}] -> Using 'cuda'"
                    )
                else:
                    logger.info(
                        f"Detected NVIDIA GPU (CUDA) -> "
                        f"[{torch.cuda.get_device_name(0)}] -> Using 'cuda'"
                    )

            except Exception as name_err:
                # 即使取得裝置名稱失敗，只要 CUDA 可用仍然可以使用
                logger.warning(
                    f"CUDA is available, but failed to get device name: "
                    f"{name_err}"
                )

            return "cuda"

        # Intel Arc / Intel GPU
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            logger.info(
                "Detected Intel GPU (Arc/Flex) -> Using 'xpu'"
            )
            return torch.device("xpu")

        # Apple Silicon / MPS
        if (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        ):
            logger.info(
                "Detected Apple Silicon backend -> Using 'mps'"
            )
            return "mps"

        # CPU fallback
        logger.info(
            "No GPU acceleration detected -> Falling back to 'cpu'"
        )
        return "cpu"

    except Exception as e:
        logger.error(
            f"Error occurred during GPU device detection: {e}. "
            f"Defaulting to 'cpu'",
            exc_info=True,
        )
        return "cpu"


def get_gpu_dtype() -> torch.dtype:
    """自動偵測目前裝置適合使用的數據精度。

    支援硬體：
    - NVIDIA GPU / AMD ROCm (CUDA): 優先使用 bfloat16
    - Intel XPU: 優先使用 bfloat16
    - Apple Silicon MPS: 使用 float16
    - CPU: 使用 float32
    """
    try:
        device = get_gpu_device()

        # 統一轉成字串處理
        device_str = str(device).lower()

        # NVIDIA / AMD ROCm
        if "cuda" in device_str:
            if (
                hasattr(torch.cuda, "is_bf16_supported")
                and torch.cuda.is_bf16_supported()
            ):
                logger.debug(
                    "CUDA supports bfloat16 -> "
                    "Using 'torch.bfloat16'"
                )
                return torch.bfloat16

            logger.debug(
                "CUDA does not support bfloat16 -> "
                "Falling back to 'torch.float16'"
            )
            return torch.float16

        # Intel XPU
        elif "xpu" in device_str:
            if (
                hasattr(torch.xpu, "is_bf16_supported")
                and torch.xpu.is_bf16_supported()
            ):
                logger.debug(
                    "XPU supports bfloat16 -> "
                    "Using 'torch.bfloat16'"
                )
                return torch.bfloat16

            logger.info(
                "XPU using 'torch.float16'"
            )
            return torch.float16

        # Apple Silicon
        elif "mps" in device_str:
            logger.debug(
                "MPS detected -> Using 'torch.float16'"
            )
            return torch.float16

        # CPU
        else:
            logger.debug(
                "CPU detected -> Using 'torch.float32' for safety"
            )
            return torch.float32

    except Exception as e:
        logger.error(
            f"Error occurred during GPU dtype detection: {e}. "
            f"Defaulting to 'torch.float32'",
            exc_info=True,
        )
        return torch.float32


def log_device_memory(
        device: Any,
        component: str = "unknown",
        stage: str = "",
        log_level: int = logging.DEBUG,
) -> None:
    """記錄目前 Process 的 CPU RAM 與 GPU 記憶體使用狀況。

    Args:
        device:
            PyTorch 使用中的裝置，例如：
            - "cuda"
            - "mps"
            - "xpu"
            - "cpu"

        component:
            記錄目前是哪個 Component / Model / Factory。

            例如：
            - "maskrcnn_model"
            - "yolo11n"
            - "stable-diffusion-v1-5"
            - "clip-ViT-B-32"
            - "detection_factory"
            - "transform_factory"

            使用 component 而不是 model，
            因為此 function 不一定只記錄單一模型。

        stage:
            記錄目前 memory snapshot 所處的階段。

            例如：
            - "before_load"
            - "after_load"
            - "before_inference"
            - "after_inference"
            - "before_clear_cache"
            - "after_clear_cache"

        log_level:
            設定 memory log 的 logging level。

            例如：
                logging.DEBUG
                logging.INFO

            預設使用 DEBUG，避免 production INFO log
            被大量 memory log 淹沒。

    ------------------------------------------------------------------
    CPU / System Memory
    ------------------------------------------------------------------

    process_rss:
        目前 Python Process 實際佔用的 RAM。

        包含 Python、模型、framework、native library 等
        該 Process 持有的 resident memory。

    system_used:
        整台作業系統目前使用中的 RAM。

        不只包含目前 Python Process，也包含其他 Process、
        OS、cache 等。

    system_available:
        作業系統目前估計可以提供給新的 Process 使用的 RAM。

        通常比單純的：
            system_total - system_used

        更有參考價值。

    system_total:
        整台機器的實體 RAM 總容量。

    ------------------------------------------------------------------
    CUDA / NVIDIA / AMD ROCm
    ------------------------------------------------------------------

    allocated:
        PyTorch 目前實際被 Tensor 使用的 GPU memory。

    reserved:
        PyTorch caching allocator 保留的 GPU memory。

        通常：
            reserved >= allocated

        allocated:
            目前 Tensor 正在使用。

        reserved:
            PyTorch 已向 GPU allocator 取得，
            即使目前沒有 Tensor 使用，也可能暫時保留，
            以便下一次運算快速重新利用。

    peak_allocated:
        自上次 reset_peak_memory_stats() 之後，
        PyTorch Tensor 使用過的最高 GPU memory。

    peak_reserved:
        自上次 reset_peak_memory_stats() 之後，
        PyTorch caching allocator 曾經保留過的最高 GPU memory。

    total:
        GPU 實體 VRAM 總容量。

    ------------------------------------------------------------------
    MPS / Apple Silicon
    ------------------------------------------------------------------

    allocated:
        PyTorch 目前配置給 MPS Tensor 使用的 GPU memory。

        Apple Silicon 使用 Unified Memory Architecture，
        CPU 與 GPU 共用系統 RAM，因此不能完全等同於
        NVIDIA 獨立 VRAM。

    driver_allocated:
        Metal / MPS driver 層級目前配置的 GPU memory。

        通常會比 PyTorch 的 allocated 大，
        因為可能還包含：

        - Metal buffer
        - MPS framework 資源
        - GPU driver 資源
        - allocator / cache
        - 其他 GPU execution 所需的 memory

        因此 Apple Silicon 上，
        driver_allocated 通常比 allocated 更接近
        GPU / Metal 實際管理的 memory 使用情況。

    ------------------------------------------------------------------
    Intel XPU
    ------------------------------------------------------------------

    allocated:
        PyTorch Tensor 目前實際使用的 XPU memory。

    reserved:
        PyTorch XPU caching allocator 目前保留的 memory。

    ------------------------------------------------------------------
    注意事項
    ------------------------------------------------------------------

    - 不同硬體平台的 memory API 定義並不完全相同。
    - CUDA 的 allocated / reserved 與 MPS 的 allocated /
      driver_allocated 不能直接視為完全等價的指標。
    - Apple Silicon 使用 Unified Memory，因此 MPS memory
      同時會影響整體 system RAM。
    - 比較模型 / Component memory 時，建議搭配：
        1. process_rss
        2. system_available
        3. GPU allocated
        4. GPU driver_allocated
      一起觀察。
    - 分析 inference peak memory 時，CUDA 可搭配
      peak_allocated / peak_reserved。
    - MPS 沒有與 CUDA 完全等價的 peak memory API，
      因此主要觀察 inference 前後的：
        allocated
        driver_allocated
        process_rss
        system_available
    """

    try:
        device_str = str(device).lower()

        # ==========================================================
        # CPU / System Memory
        # ==========================================================

        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss

        virtual_memory = psutil.virtual_memory()

        cpu_process_rss = process_memory / 1024 ** 3
        cpu_system_used = virtual_memory.used / 1024 ** 3
        cpu_system_available = virtual_memory.available / 1024 ** 3
        cpu_system_total = virtual_memory.total / 1024 ** 3

        # ==========================================================
        # CUDA
        # ==========================================================

        if "cuda" in device_str:
            if not torch.cuda.is_available():
                logger.warning(
                    "log_device_memory: device='%s' "
                    "但 CUDA 不可用，略過 GPU memory",
                    device,
                )

                logger.log(
                    log_level,
                    "[Memory][%s][%s] "
                    "CPU: process_rss=%.2f GB | "
                    "system_used=%.2f GB | "
                    "system_available=%.2f GB | "
                    "system_total=%.2f GB",
                    component,
                    stage,
                    cpu_process_rss,
                    cpu_system_used,
                    cpu_system_available,
                    cpu_system_total,
                )
                return

            if (
                isinstance(device, torch.device)
                and device.index is not None
            ):
                device_index = device.index
            else:
                device_index = torch.cuda.current_device()

            allocated = torch.cuda.memory_allocated(device_index)
            reserved = torch.cuda.memory_reserved(device_index)

            peak_allocated = torch.cuda.max_memory_allocated(
                device_index
            )
            peak_reserved = torch.cuda.max_memory_reserved(
                device_index
            )

            total = torch.cuda.get_device_properties(
                device_index
            ).total_memory

            logger.log(
                log_level,
                "[Memory][%s][%s] "
                "CPU: process_rss=%.2f GB | "
                "system_used=%.2f GB | "
                "system_available=%.2f GB | "
                "system_total=%.2f GB | "
                "GPU: device=%s | "
                "allocated=%.2f GB | "
                "reserved=%.2f GB | "
                "peak_allocated=%.2f GB | "
                "peak_reserved=%.2f GB | "
                "total=%.2f GB",
                component,
                stage,
                cpu_process_rss,
                cpu_system_used,
                cpu_system_available,
                cpu_system_total,
                device,
                allocated / 1024 ** 3,
                reserved / 1024 ** 3,
                peak_allocated / 1024 ** 3,
                peak_reserved / 1024 ** 3,
                total / 1024 ** 3,
            )

        # ==========================================================
        # MPS
        # ==========================================================

        elif "mps" in device_str:
            if not torch.backends.mps.is_available():
                logger.warning(
                    "log_device_memory: device='%s' "
                    "但 MPS 不可用，略過 GPU memory",
                    device,
                )

                logger.log(
                    log_level,
                    "[Memory][%s][%s] "
                    "CPU: process_rss=%.2f GB | "
                    "system_used=%.2f GB | "
                    "system_available=%.2f GB | "
                    "system_total=%.2f GB",
                    component,
                    stage,
                    cpu_process_rss,
                    cpu_system_used,
                    cpu_system_available,
                    cpu_system_total,
                )
                return

            allocated = torch.mps.current_allocated_memory()
            driver_allocated = torch.mps.driver_allocated_memory()

            logger.log(
                log_level,
                "[Memory][%s][%s] "
                "CPU: process_rss=%.2f GB | "
                "system_used=%.2f GB | "
                "system_available=%.2f GB | "
                "system_total=%.2f GB | "
                "GPU: device=%s | "
                "allocated=%.2f GB | "
                "driver_allocated=%.2f GB",
                component,
                stage,
                cpu_process_rss,
                cpu_system_used,
                cpu_system_available,
                cpu_system_total,
                device,
                allocated / 1024 ** 3,
                driver_allocated / 1024 ** 3,
            )

        # ==========================================================
        # Intel XPU
        # ==========================================================

        elif "xpu" in device_str:
            if (
                not hasattr(torch, "xpu")
                or not torch.xpu.is_available()
            ):
                logger.warning(
                    "log_device_memory: device='%s' "
                    "但 XPU 不可用，略過 GPU memory",
                    device,
                )

                logger.log(
                    log_level,
                    "[Memory][%s][%s] "
                    "CPU: process_rss=%.2f GB | "
                    "system_used=%.2f GB | "
                    "system_available=%.2f GB | "
                    "system_total=%.2f GB",
                    component,
                    stage,
                    cpu_process_rss,
                    cpu_system_used,
                    cpu_system_available,
                    cpu_system_total,
                )
                return

            allocated = torch.xpu.memory_allocated()
            reserved = torch.xpu.memory_reserved()

            logger.log(
                log_level,
                "[Memory][%s][%s] "
                "CPU: process_rss=%.2f GB | "
                "system_used=%.2f GB | "
                "system_available=%.2f GB | "
                "system_total=%.2f GB | "
                "GPU: device=%s | "
                "allocated=%.2f GB | "
                "reserved=%.2f GB",
                component,
                stage,
                cpu_process_rss,
                cpu_system_used,
                cpu_system_available,
                cpu_system_total,
                device,
                allocated / 1024 ** 3,
                reserved / 1024 ** 3,
            )

        # ==========================================================
        # CPU
        # ==========================================================

        elif "cpu" in device_str:
            logger.log(
                log_level,
                "[Memory][%s][%s] "
                "CPU: process_rss=%.2f GB | "
                "system_used=%.2f GB | "
                "system_available=%.2f GB | "
                "system_total=%.2f GB",
                component,
                stage,
                cpu_process_rss,
                cpu_system_used,
                cpu_system_available,
                cpu_system_total,
            )

        # ==========================================================
        # Unknown
        # ==========================================================

        else:
            logger.warning(
                "[Memory][%s][%s] Unknown device=%s | "
                "CPU: process_rss=%.2f GB | "
                "system_used=%.2f GB | "
                "system_available=%.2f GB | "
                "system_total=%.2f GB",
                component,
                stage,
                device,
                cpu_process_rss,
                cpu_system_used,
                cpu_system_available,
                cpu_system_total,
            )

    except Exception as e:
        logger.error(
            f"Error occurred while reading device memory: {e}",
            exc_info=True,
        )


def clear_device_cache(device: Any) -> None:
    """
    釋放指定裝置上，PyTorch 快取分配器持有但目前未使用的記憶體。

    注意：
    - 不會回收仍被引用中的 tensor
    - 不是萬能的 memory leak 解法
    - 頻繁呼叫會有額外的重新分配開銷
    - 建議只在切換模型或批次處理之間呼叫
    - 不建議每次 forward 都呼叫
    """
    try:
        device_str = str(device).lower()

        # CUDA
        if "cuda" in device_str:
            if not torch.cuda.is_available():
                logger.warning(
                    "clear_device_cache: "
                    "device='%s' 但 CUDA 不可用，略過",
                    device,
                )
                return

            torch.cuda.synchronize()
            torch.cuda.empty_cache()

            # CUDA IPC
            if hasattr(torch.cuda, "ipc_collect"):
                torch.cuda.ipc_collect()

            logger.debug(
                "CUDA cache cleared"
            )

        # MPS
        elif "mps" in device_str:
            if not torch.backends.mps.is_available():
                logger.warning(
                    "clear_device_cache: "
                    "device='%s' 但 MPS 不可用，略過",
                    device,
                )
                return

            torch.mps.empty_cache()

            logger.debug(
                "MPS cache cleared"
            )

        # XPU
        elif "xpu" in device_str:
            if (
                hasattr(torch, "xpu")
                and torch.xpu.is_available()
            ):
                torch.xpu.empty_cache()

                logger.debug(
                    "XPU cache cleared"
                )
            else:
                logger.warning(
                    "clear_device_cache: "
                    "device='%s' 但 XPU 不可用，略過",
                    device,
                )

        # CPU
        elif "cpu" in device_str:
            gc.collect()

            logger.debug(
                "CPU: triggered gc.collect()"
            )

        # Unknown
        else:
            logger.warning(
                "clear_device_cache: "
                "未知的 device='%s'，略過",
                device,
            )

    except Exception as e:
        logger.error(
            f"Error occurred while clearing device cache: {e}",
            exc_info=True,
        )