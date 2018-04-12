def decorator_function(original_method):
    def wrapper_functiom(instance):
        return original_method(instance)
    return wrapper_functiom

class Person:
    def __init__(self, name):
        self.name = name
    @decorator_function
    def print_name(self, age):
        print(self.name, age)

p1 = Person('eddard')
p1.print_name(25)
p2 = Person('joffrey')
p2.print_name(13)