import time
from backend.core.websockets.connection_manager import manager

LOCK_TIMEOUT_SECONDS = 15

class LockService:
    def get_locked_elements(self, sala_id: str):
        if sala_id in manager.salas:
            self._cleanup_stale_locks(sala_id)
            return manager.salas[sala_id].get("locked_elements", {})
        return {}

    def lock_element(self, sala_id: str, element_id: str, user_id: str, nickname: str):
        if sala_id in manager.salas:
            self._cleanup_stale_locks(sala_id)
            locked = manager.salas[sala_id].get("locked_elements", {})
            # Si no está bloqueado, o si ya lo tiene este mismo usuario
            if element_id not in locked or locked[element_id]["user_id"] == user_id:
                locked[element_id] = {
                    "user_id": user_id, 
                    "nickname": nickname,
                    "last_active": time.time()
                }
                manager.salas[sala_id]["locked_elements"] = locked
                return True
        return False

    def refresh_lock(self, sala_id: str, element_id: str, user_id: str):
        if sala_id in manager.salas:
            locked = manager.salas[sala_id].get("locked_elements", {})
            if element_id in locked and locked[element_id]["user_id"] == user_id:
                locked[element_id]["last_active"] = time.time()
                return True
        return False

    def unlock_element(self, sala_id: str, element_id: str, user_id: str):
        if sala_id in manager.salas:
            locked = manager.salas[sala_id].get("locked_elements", {})
            if element_id in locked and locked[element_id]["user_id"] == user_id:
                del locked[element_id]
                manager.salas[sala_id]["locked_elements"] = locked
                return True
        return False

    def _cleanup_stale_locks(self, sala_id: str):
        if sala_id in manager.salas:
            locked = manager.salas[sala_id].get("locked_elements", {})
            current_time = time.time()
            stale_keys = [k for k, v in locked.items() if current_time - v.get("last_active", 0) > LOCK_TIMEOUT_SECONDS]
            for k in stale_keys:
                del locked[k]
            if stale_keys:
                manager.salas[sala_id]["locked_elements"] = locked

    def get_stale_locks(self, sala_id: str) -> list:
        stale_keys = []
        if sala_id in manager.salas:
            locked = manager.salas[sala_id].get("locked_elements", {})
            current_time = time.time()
            stale_keys = [k for k, v in locked.items() if current_time - v.get("last_active", 0) > LOCK_TIMEOUT_SECONDS]
        return stale_keys

lock_service = LockService()
