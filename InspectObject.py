import sys

def InspectObject(obj):
    """
    Inspect any object, printing its methods and attributes.
    
    Args:
        obj: The object to inspect
    """
    if obj is None:
        print("Cannot inspect None object")
        return
        
    obj_type = type(obj)
    print(f"Object of type: {obj_type.__name__}")
    
    # Get methods and attributes
    methods = []
    attributes = []
    
    for name in dir(obj):
        if name.startswith('_'):
            continue
            
        try:
            attr = getattr(obj, name)
            if callable(attr):
                methods.append(name)
            else:
                attributes.append(name)
        except Exception:
            pass
    
    # Print methods
    print("Methods:")
    for method in sorted(methods):
        print(f"  - {method}()")
        
    # Print attributes
    print("Attributes:")
    for attr in sorted(attributes):
        print(f"  - {attr}")