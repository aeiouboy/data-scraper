"""
Progress bar utilities for cleaner console output
"""
from typing import Optional
import sys


class ProgressBar:
    """Simple progress bar for console output"""
    
    def __init__(self, total: int, prefix: str = "", width: int = 50):
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
        
    def update(self, current: int, suffix: str = ""):
        """Update progress bar"""
        self.current = current
        percent = 100 * (current / float(self.total))
        filled = int(self.width * current // self.total)
        bar = "█" * filled + "-" * (self.width - filled)
        
        # Clear line and print progress
        sys.stdout.write("\r")
        sys.stdout.write(f"{self.prefix} |{bar}| {percent:.1f}% {suffix}")
        sys.stdout.flush()
        
        # New line when complete
        if current >= self.total:
            print()
    
    def increment(self, suffix: str = ""):
        """Increment progress by 1"""
        self.update(self.current + 1, suffix)