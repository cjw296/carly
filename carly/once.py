class Once:

    def __init__(self, target):
        self.target = target
        self.called = False

    def __call__(self, *args, **kw):
        if self.called:
            return
        self.called = True
        return self.target(*args, **kw)
