class User:
    def __init__(self, id, username, module, is_admin, can_edit_bo=1, can_delete_bo=1, can_track_bo=1):
        self.id = id
        self.username = username
        self.module = module
        self.is_admin = self._to_bool(is_admin)
        self.can_edit_bo = self._to_bool(can_edit_bo)
        self.can_delete_bo = self._to_bool(can_delete_bo)
        self.can_track_bo = self._to_bool(can_track_bo)

    @staticmethod
    def _to_bool(value):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "sim", "yes"}
        return bool(value)

    def can_edit(self):
        return self.is_admin or self.can_edit_bo

    def can_delete(self):
        return self.is_admin or self.can_delete_bo

    def can_track(self):
        return self.is_admin or self.can_track_bo

    def get_allowed_modules(self):
        modulo = str(self.module)
        if modulo == "0":
            return ["Corporativo"]
        if modulo == "1":
            return ["Varejo"]
        if modulo == "2":
            return ["Exportação"]
        if modulo == "3":
            return ["Corporativo", "Varejo"]
        if modulo == "4":
            return ["Corporativo", "Varejo", "Exportação"]
        return []

    def has_multiple_modules(self):
        return len(self.get_allowed_modules()) > 1

    def __repr__(self):
        return f"<User {self.username} ({'Admin' if self.is_admin else 'Comum'})>"