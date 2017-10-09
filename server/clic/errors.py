
class UserError(Exception):
    """An error that should be shown as a regular message to user"""

    def __init__(self, message, level):
        super(UserError, self).__init__(message)
        self.level = level
        self.print_stack = False
