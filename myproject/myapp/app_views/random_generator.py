import random

def generate_lottery_numbers():
    # Generate 6 unique random numbers between 1 and 49
    lottery_numbers = random.sample(range(1, 56), 6)
    return sorted(lottery_numbers)

if __name__ == "__main__":
    random_numbers = generate_lottery_numbers()
    print("Randomly generated lottery numbers:", random_numbers)
