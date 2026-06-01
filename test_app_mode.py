#!/usr/bin/env python3
"""
Test script to simulate what happens when the Flask app is started multiple times.
This tests the mode assignment as it would happen in the actual app.
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.append('/home/ssegal/Flask_website')

from backend.services.mode_assignment import add_intervention

def simulate_app_start():
    """Simulate what happens when the app starts up."""
    # This is what happens in app.py when /mode route is called for a new session
    mode = add_intervention()
    return mode

def test_multiple_app_starts():
    """Test multiple app starts to see if we get proper randomization."""
    print("Simulating multiple app starts (like when users visit the site):")
    modes = []
    
    for i in range(20):
        mode = simulate_app_start()
        modes.append(mode)
        group_name = "Treatment" if mode == 1 else "Control"
        print(f"User {i+1}: {group_name} (mode={mode})")
    
    # Analyze results
    control_count = modes.count(0)
    treatment_count = modes.count(1)
    
    print(f"\nResults:")
    print(f"Control group (mode=0): {control_count} users ({control_count/len(modes)*100:.1f}%)")
    print(f"Treatment group (mode=1): {treatment_count} users ({treatment_count/len(modes)*100:.1f}%)")
    
    if control_count > 0 and treatment_count > 0:
        print("✅ Randomization is working properly!")
    else:
        print("⚠️  Warning: All users got the same mode - this suggests an issue!")

if __name__ == "__main__":
    test_multiple_app_starts()