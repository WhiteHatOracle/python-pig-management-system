import random

numbers = [str(random.randint(40, 110)) for _ in range(40)]
result = ",".join(numbers)

print(result)
