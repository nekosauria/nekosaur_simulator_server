import gc
import logging
import os
import random
from functools import lru_cache

import psutil
import torch

from util.common import common


logger = common.logger
config = common.config


# ==========================================================
# Hardware Detection
# ==========================================================

@lru_cache(maxsize=1)
def get_gpu_device() -> torch.device:
    """偵測目前可使用的硬體加速裝置。

    優先序：
        NVIDIA / AMD ROCm (CUDA) -> Intel XPU -> Apple Silicon MPS -> CPU

    使用 lru_cache(maxsize=1)：
    - 第一次呼叫時實際偵測硬體
    - 後續呼叫直接回傳 cache
    - 同一個 Python process 內不會重複偵測
    """
    selected_device = torch.device("cpu")
    detail_msg = "CPU fallback"

    try:
        # 1. NVIDIA GPU / AMD ROCm (透過 torch.cuda API 使用)
        if torch.cuda.is_available():
            try:
                device_name = torch.cuda.get_device_name(0)
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

                if "amd" in device_name.lower() or "radeon" in device_name.lower():
                    detail_msg = f"AMD GPU (ROCm) [{device_name}], VRAM: {vram_gb:.2f} GB"
                else:
                    detail_msg = f"NVIDIA GPU (CUDA) [{device_name}], VRAM: {vram_gb:.2f} GB"

            except Exception as name_err:
                logger.warning("CUDA is available, but failed to get device properties: %s", name_err)
                detail_msg = "CUDA device (Failed to get properties)"

            selected_device = torch.device("cuda")

        # 2. Intel XPU (Arc / Flex)
        elif hasattr(torch, "xpu") and torch.xpu.is_available():
            selected_device = torch.device("xpu")
            detail_msg = "Intel GPU (Arc/Flex)"

        # 3. Apple Silicon / MPS
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            selected_device = torch.device("mps")
            detail_msg = "Apple Silicon MPS Acceleration"

        # 4. CPU Fallback
        else:
            selected_device = torch.device("cpu")
            detail_msg = "No GPU acceleration detected"

        # 印出最終選定硬體的 Summary Log
        logger.info("=" * 60)
        logger.info("[Device Init Summary] Selected Target Device: [%s]", selected_device)
        logger.info("[Device Init Summary] Hardware Details: %s", detail_msg)
        logger.info("=" * 60)

        return selected_device

    except Exception as e:
        logger.error(
            "Error occurred during GPU device detection: %s. Defaulting to 'cpu'",
            e,
            exc_info=True,
        )
        return torch.device("cpu")

@lru_cache(maxsize=1)
def get_gpu_dtype() -> torch.dtype:
    """自動偵測目前裝置適合使用的數據精度。

    支援：

    CUDA / NVIDIA / AMD ROCm:
        優先使用 bfloat16
        不支援時 fallback 到 float16

    Intel XPU:
        優先使用 bfloat16
        不支援時 fallback 到 float16

    Apple Silicon / MPS:
        使用 float16

    CPU:
        使用 float32

    dtype 只會在第一次呼叫時實際偵測。
    後續呼叫直接使用 lru_cache。
    """
    try:
        device = get_gpu_device()

        # ======================================================
        # CUDA / NVIDIA / AMD ROCm
        # ======================================================

        if device.type == "cuda":
            if (
                hasattr(torch.cuda, "is_bf16_supported")
                and torch.cuda.is_bf16_supported()
            ):
                logger.debug(
                    "CUDA supports bfloat16 -> Using 'torch.bfloat16'"
                )

                return torch.bfloat16

            logger.debug(
                "CUDA does not support bfloat16 -> "
                "Falling back to 'torch.float16'"
            )

            return torch.float16

        # ======================================================
        # Intel XPU
        # ======================================================

        if device.type == "xpu":
            if (
                hasattr(torch.xpu, "is_bf16_supported")
                and torch.xpu.is_bf16_supported()
            ):
                logger.debug(
                    "XPU supports bfloat16 -> Using 'torch.bfloat16'"
                )

                return torch.bfloat16

            logger.debug(
                "XPU does not support bfloat16 -> "
                "Using 'torch.float16'"
            )

            return torch.float16

        # ======================================================
        # Apple Silicon / MPS
        # ======================================================

        if device.type == "mps":
            logger.debug(
                "MPS detected -> Using 'torch.float16'"
            )

            return torch.float16

        # ======================================================
        # CPU
        # ======================================================

        logger.debug(
            "CPU detected -> Using 'torch.float32' for safety"
        )

        return torch.float32

    except Exception as e:
        logger.error(
            "Error occurred during GPU dtype detection: %s. "
            "Defaulting to 'torch.float32'",
            e,
            exc_info=True,
        )

        return torch.float32


# ==========================================================
# Device Memory Logging
# ==========================================================

def log_device_memory(
        device: torch.device,
        component: str = "unknown",
        stage: str = "",
        log_level: int = logging.DEBUG,
) -> None:
    """記錄目前 Process 的 CPU RAM 與 GPU 記憶體使用狀況。

    Args:
        device:
            PyTorch 使用中的裝置。

            例如：
                torch.device("cuda")
                torch.device("mps")
                torch.device("xpu")
                torch.device("cpu")

        component:
            記錄目前是哪個 Component / Model / Factory。

            例如：
                "maskrcnn_model"
                "yolo11n"
                "stable-diffusion"
                "clip"
                "detection_factory"
                "transform_factory"

            使用 component 而不是 model，
            因為此 function 不一定只記錄單一模型。

        stage:
            記錄目前 memory snapshot 所處的階段。

            例如：
                "before_load"
                "after_load"
                "before_inference"
                "after_inference"
                "before_clear_cache"
                "after_clear_cache"

        log_level:
            logging level。

            例如：
                logging.DEBUG
                logging.INFO

            預設使用 DEBUG，
            避免 production INFO log 被大量 memory log 淹沒。

    ------------------------------------------------------------------
    CPU / System Memory
    ------------------------------------------------------------------

    process_rss:
        目前 Python Process 實際佔用的 RAM。

    system_used:
        整台作業系統目前使用中的 RAM。

    system_available:
        作業系統目前估計可以提供給新的 Process 使用的 RAM。

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

        通常會比 PyTorch allocated 大，
        因為可能還包含：

        - Metal buffer
        - MPS framework 資源
        - GPU driver 資源
        - allocator / cache
        - 其他 GPU execution 所需的 memory

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
      driver_allocated 不能直接視為完全等價。
    - Apple Silicon 使用 Unified Memory，因此 MPS memory
      同時會影響整體 system RAM。
    - 比較模型 / Component memory 時，建議搭配：
        1. process_rss
        2. system_available
        3. GPU allocated
        4. GPU driver_allocated
      一起觀察。
    - 分析 inference peak memory 時，CUDA 可搭配：
        peak_allocated
        peak_reserved
    - MPS 沒有與 CUDA 完全等價的 peak memory API，
      因此主要觀察：
        allocated
        driver_allocated
        process_rss
        system_available
    """

    try:
        # ======================================================
        # Normalize device
        # ======================================================

        if not isinstance(device, torch.device):
            device = torch.device(device)

        device_type = device.type

        # ======================================================
        # CPU / System Memory
        # ======================================================

        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss

        virtual_memory = psutil.virtual_memory()

        cpu_process_rss = process_memory / 1024 ** 3
        cpu_system_used = virtual_memory.used / 1024 ** 3
        cpu_system_available = virtual_memory.available / 1024 ** 3
        cpu_system_total = virtual_memory.total / 1024 ** 3

        # ======================================================
        # CUDA
        # ======================================================

        if device_type == "cuda":

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

            # 若 device 沒指定 index，例如 cuda，
            # 使用目前 PyTorch active device。
            device_index = (
                device.index
                if device.index is not None
                else torch.cuda.current_device()
            )

            allocated = torch.cuda.memory_allocated(
                device_index
            )

            reserved = torch.cuda.memory_reserved(
                device_index
            )

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

        # ======================================================
        # MPS
        # ======================================================

        elif device_type == "mps":

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

        # ======================================================
        # Intel XPU
        # ======================================================

        elif device_type == "xpu":

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

        # ======================================================
        # CPU
        # ======================================================

        elif device_type == "cpu":

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

        # ======================================================
        # Unknown
        # ======================================================

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
            "Error occurred while reading device memory: %s",
            e,
            exc_info=True,
        )


# ==========================================================
# Device Cache Management
# ==========================================================

def clear_device_cache(
        device: torch.device,
) -> None:
    """釋放指定裝置上 PyTorch caching allocator
    持有但目前未使用的記憶體。

    注意：

    - 不會回收仍被 Python / Tensor reference 持有的 memory
    - 不是 memory leak 的萬能解法
    - 頻繁呼叫可能造成額外的 allocation overhead
    - GPU inference 不建議每次 forward 都呼叫
    - 適合用在模型切換、batch / request 階段結束時
    """

    try:
        # ======================================================
        # Normalize device
        # ======================================================

        if not isinstance(device, torch.device):
            device = torch.device(device)

        device_type = device.type

        # ======================================================
        # CUDA
        # ======================================================

        if device_type == "cuda":

            if not torch.cuda.is_available():
                logger.warning(
                    "clear_device_cache: "
                    "device='%s' 但 CUDA 不可用，略過",
                    device,
                )

                return

            # 確保 GPU operations 已完成，
            # 再進行 cache 清理。
            torch.cuda.synchronize(device)

            # 釋放 caching allocator 中目前沒有被 Tensor 使用的 memory。
            torch.cuda.empty_cache()

            # 嘗試釋放 CUDA IPC 資源。
            if hasattr(torch.cuda, "ipc_collect"):
                torch.cuda.ipc_collect()

            logger.debug(
                "CUDA cache cleared"
            )

        # ======================================================
        # MPS
        # ======================================================

        elif device_type == "mps":

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

        # ======================================================
        # Intel XPU
        # ======================================================

        elif device_type == "xpu":

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

        # ======================================================
        # CPU
        # ======================================================

        elif device_type == "cpu":

            gc.collect()

            logger.debug(
                "CPU: triggered gc.collect()"
            )

        # ======================================================
        # Unknown
        # ======================================================

        else:

            logger.warning(
                "clear_device_cache: "
                "未知的 device='%s'，略過",
                device,
            )

    except Exception as e:
        logger.error(
            "Error occurred while clearing device cache: %s",
            e,
            exc_info=True,
        )


# ==========================================================
# Device Cache + Memory Logging
# ==========================================================

def clear_device_cache_with_log(
        device: torch.device,
        component: str,
        log_level: int = logging.DEBUG,
) -> None:
    """清理 device cache，並記錄清理前後的 memory 使用量。

    執行流程：

        before_clear_cache
            ↓
        clear_device_cache()
            ↓
        after_clear_cache
    """

    logger.debug(
        "clear_device_cache_with_log: "
        "device=%s, component=%s, log_level=%s",
        device,
        component,
        log_level,
    )

    # ======================================================
    # Before
    # ======================================================

    log_device_memory(
        device,
        component=component,
        stage="before_clear_cache",
        log_level=log_level,
    )

    # ======================================================
    # Clear
    # ======================================================

    clear_device_cache(device)

    # ======================================================
    # After
    # ======================================================

    log_device_memory(
        device,
        component=component,
        stage="after_clear_cache",
        log_level=log_level,
    )


# ==========================================================
# Torch Random Generator
# ==========================================================

def get_torch_generator(
        seed: int | None = None, device: str | torch.device = "cpu"
) -> tuple[torch.Generator, int]:
    """
    建立獨立且執行緒安全的 PyTorch Generator

    :param seed: 指定隨機種子，若為 None 則自動生成
    :param device: 執行的裝置 ("cpu", "cuda", "mps")
    :return: (torch.Generator 物件, 實際使用的 seed 整數)
    """
    # 若未指定 seed，產生一個 32-bit 無符號整數範圍內的隨機 Seed
    actual_seed = seed if seed is not None else random.randint(0, 2 ** 32 - 1)

    # 建立指定 device 的 Generator 並帶入 seed
    generator = torch.Generator(device=device).manual_seed(actual_seed)

    return generator, actual_seed