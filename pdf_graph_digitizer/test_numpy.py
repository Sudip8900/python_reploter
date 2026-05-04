import numpy as np
a = np.uint8(200)
try:
    print(a + 60)
except Exception as e:
    print("Error:", e)

b = np.array([200], dtype=np.uint8)
try:
    print(b[0] + 60)
except Exception as e:
    print("Error:", e)

print("Type of b[0]:", type(b[0]))
