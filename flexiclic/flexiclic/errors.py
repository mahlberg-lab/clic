class UserError(Exception):
    """An error that should be shown as a regular message to user"""

    def __init__(self, message, level):
        """
        - message: Message to display to the user
        - level: Severity of message, info/warn/error
        """
        super(UserError, self).__init__(message)
        self.level = level
        self.print_stack = False


class UserConfirmError(Exception):
    """Not an error, but instead user should confirm to continue"""

    def __init__(self):
        super(UserConfirmError, self).__init__("Confirm to continue processing")
        self.print_stack = False
