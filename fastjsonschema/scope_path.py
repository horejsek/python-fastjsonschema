class ScopePath():
    def __init__(self, cur_path, tail):
        self.cur_path = cur_path
        self.tail = tail

    def __enter__(self):
        if self.tail is not None:
            self.cur_path.append(str(self.tail))

    def __exit__(self, type_, value, traceback):
        if self.tail is not None:
            self.cur_path.pop()