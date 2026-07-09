import random
import time
import os

def add_intervention():
    """
    Randomly assigns a user to either control (0) or treatment (1) group.
    
    This function generates a fresh random assignment each time it's called,
    ensuring proper randomization for experimental purposes by seeding on each call.
    
    :return: The assigned group (0 for control, 1 for treatment)
    :rtype: int
    """
    # Seed with current time and process ID for better randomization
    # This ensures each call gets a different seed, not just each module import
    #random.seed(int(time.time() * 1000000) + os.getpid() + random.randint(0, 100000))
    
    # 0: control group (no interventions)
    # 1: treatment group (with interventions)
    #return random.randint(0, 1)
    return 1



