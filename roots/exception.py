

class ExtractException(Exception):

    def __init__(self, *args):
        self.string = '\n'.join(map(str, args))
    def __str__(self):
        return self.string

