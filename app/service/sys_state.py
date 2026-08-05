from dao.sys_state import get_count
from entity.sys_state import SysState


def get_image_process_count(state: SysState):
    return get_count(state)