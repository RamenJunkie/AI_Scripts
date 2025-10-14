# An Extremely Inefficient Hello Worls Program
# Created with Claude.ai

#!/usr/bin/env python3
import random
import string
import time
import sys

def generate_random_string(length):
    """Generate a random string of specified length"""
    # Define the character set to use (lowercase, uppercase, space, and punctuation)
    chars = string.ascii_letters + ' ' + ',.!?;:'
    
    # Generate the random string
    return ''.join(random.choice(chars) for _ in range(length))

def check_match(random_string, target="Hello World"):
    """Check if the random string matches the target"""
    return random_string == target

def main():
    # Define the target string
    target = "Hello World"
    target_length = len(target)
    
    # Set up counters
    attempts = 0
    start_time = time.time()
    check_interval = 1000000  # How often to print status
    
    print(f"Target string: '{target}'")
    print(f"Target length: {target_length}")
    print(f"Starting random string generation...")
    print(f"Status updates every {check_interval:,} attempts")
    
    # Continue generating strings until we find a match
    while True:
        # Generate a random string of the same length as the target
        random_string = generate_random_string(target_length)
        
        # Increment the attempt counter
        attempts += 1
        
        # Check if the random string matches the target
        if check_match(random_string, target):
            elapsed_time = time.time() - start_time
            print(f"\nSUCCESS! Match found after {attempts:,} attempts!")
            print(f"Elapsed time: {elapsed_time:.2f} seconds")
            print(f"Random string: '{random_string}'")
            break
        
        # Print status update periodically
        if attempts % check_interval == 0:
            elapsed_time = time.time() - start_time
            rate = attempts / elapsed_time if elapsed_time > 0 else 0
            print(f"Attempts: {attempts:,} | Time: {elapsed_time:.2f}s | Rate: {rate:.2f}/s", end='\r')
            sys.stdout.flush()
    
    # Calculate and print the probability
    # For each position, we have len(chars) possibilities
    chars_count = len(string.ascii_letters + ' ' + ',.!?;:')
    total_possibilities = chars_count ** target_length
    probability = 1 / total_possibilities
    
    print(f"\nProbability of a random match: 1 in {total_possibilities:,} ({probability:.2e})")
    print(f"You got extremely lucky to see this message!")

if __name__ == "__main__":
    # Set random seed based on current time for true randomness
    random.seed(time.time())
    main()
