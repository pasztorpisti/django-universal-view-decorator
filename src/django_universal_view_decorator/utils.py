
class ClassProperty(object):
    def __init__(self, fget=None):
        super(ClassProperty, self).__init__()
        self.fget = fget

    def __get__(self, instance, owner=None):
        return self.fget(owner or type(instance))

    def getter(self, fget):
        self.fget = fget
        return self


class_property = ClassProperty
