"""Explicit test adapter; no LabVIEW or hardware API is implemented."""


class NumericReference:
    def __init__(self, value):
        self.stored_value = value
        self.events = []

    @property
    def value(self):
        self.events.append(["read", self.stored_value])
        return self.stored_value

    @value.setter
    def value(self, supplied):
        self.events.append(["write", supplied])
        self.stored_value = supplied
