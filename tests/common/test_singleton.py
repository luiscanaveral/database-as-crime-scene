from database_as_crime_scene.common.decorators.singleton import singleton
import threading

def test_singleton_basic():
    @singleton
    class MyClass:
        def __init__(self, value):
            self.value = value

    instance1 = MyClass(10)
    instance2 = MyClass(20)

    # Both instances should be exactly the same object
    assert instance1 is instance2
    # The value should be the one from the first initialization
    assert instance1.value == 10
    assert instance2.value == 10

def test_singleton_thread_safety():
    @singleton
    class MyClass:
        def __init__(self):
            # Simulate some initialization work
            import time
            time.sleep(0.01)
            self.id = threading.get_ident()

    instances = []
    
    def worker():
        instances.append(MyClass())

    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All instances retrieved in different threads should be identical
    first_instance = instances[0]
    for instance in instances[1:]:
        assert instance is first_instance
