class Event(object):

    def __init__(self):
        self.handlers = []

    def on(self, handler):
        self.handlers.append(handler)

    def once(self, handler):
        def _once(handler, *args):
            handler(*args)
            self.remove_handler(handler)

        self.on(_once)

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    def remove_all_handlers(self):
        self.handlers = []

    def __call__(self, *args):
        for handler in self.handlers:
            handler(*args)

