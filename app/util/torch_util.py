import random
import torch


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