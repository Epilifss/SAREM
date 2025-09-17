class User:
    def __init__(self, id, username, module, is_admin):
        self.id = id
        self.username = username
        self.module = module
        self.is_admin = is_admin

    def __repr__(self):
        return f"<User {self.username} ({'Admin' if self.is_admin else 'Comum'})>"