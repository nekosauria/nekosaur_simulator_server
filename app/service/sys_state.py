from entity.sys_state import SysState as SysStateEntity
from dao.sys_state import sys_state_dao # 直接引進 DAO 單例


class SysState:
    """處理圖片處理相關業務邏輯的 Service"""

    @staticmethod
    def get_image_process_count(sys_state: SysStateEntity) -> int:
        """
        取得當前正在處理/鎖定中的圖片處理數量。
        """
        # 透過單例呼叫實例方法
        return sys_state_dao.get_count(sys_state)