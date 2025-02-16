import os
from src.utils import log

class LoadScaler:
    """
    LoadScaler dynamically adjusts task concurrency based on system resources and task completion speed.

    Features:
    - Determines initial concurrency based on CPU cores if AUTO_SCALE is enabled.
    - Increases concurrency when tasks complete successfully multiple times in a row.
    - Decreases concurrency when tasks error out or time out.
    - Ensures concurrency stays within defined limits.

    Attributes:
        AUTO_SCALE (bool): Enables automatic scaling based on system resources.
        MIN_CONCURRENCY (int): The lowest concurrency allowed.
        ADAPTIVE_STEP (int): How much concurrency increases/decreases when scaling.
        ADAPTIVE_THRESHOLD (int): Number of fast completions needed to scale up.
        max_limit (int): Maximum concurrency limit (configurable).
        concurrency (int): The current concurrency level.
        fast_completions (int): Tracks consecutive successful task completions.
    """

    # Minimum concurrency to prevent zero workers
    MIN_CONCURRENCY = 1  
    # How much concurrency should increase or decrease when scaling
    ADAPTIVE_STEP = 2  
    # Number of continuous successful tasks before increasing concurrency
    ADAPTIVE_THRESHOLD = 3  

    def __init__(self, auto_scale, max_limit):
        # Whether to enable automatic scaling based on system resources
        self.AUTO_SCALE = auto_scale

        # Maximum concurrency limit to prevent excessive load
        self.max_limit = max_limit

        # Initial concurrency level (determined dynamically if auto-scaling is enabled)
        self.concurrency = self._initialize_concurrency()

        # Tracks how many tasks have completed quickly in succession
        self.fast_completions = 0  

        log(f"🔧 LoadScaler initialized with concurrency: {self.concurrency}.")

    def _initialize_concurrency(self):
        """
        Determines the initial concurrency based on system resources.

        If AUTO_SCALE is enabled:
            - Sets concurrency to 2 * CPU cores (if available) or 10 as a fallback or max limit, whichever is less.
        If AUTO_SCALE is disabled:
            - Uses the fixed max_limit from the config.
        """
        if self.AUTO_SCALE:
            # Determine the initial concurrency level based on system resources.
            # - If `os.cpu_count()` returns a valid number, we use a quarter of the available CPU cores.
            #   This ensures we don’t overload the system while keeping a good level of parallelism.
            # - If `os.cpu_count()` returns None (which happens in rare cases), we fall back to 2.
            # - We also ensure the concurrency does not exceed `self.max_limit` to maintain control.
            return max(self.MIN_CONCURRENCY, min(self.max_limit, os.cpu_count() // 4 if os.cpu_count() else 2))
        return max(self.MIN_CONCURRENCY, self.max_limit)  # Use fixed concurrency when scaling is disabled

    def adjust_concurrency(self, success):
        """
        Dynamically adjusts concurrency based on task success.

        - If tasks complete quickly multiple times in a row (>= ADAPTIVE_THRESHOLD), concurrency increases.
        - If tasks fail or time out, concurrency decreases.
        """
        if success:
            # Increase the count of consecutive fast completions
            self.fast_completions += 1  

            # If enough tasks finish quickly, increase concurrency
            if self.fast_completions >= self.ADAPTIVE_THRESHOLD and self.concurrency < self.max_limit:
                self.concurrency = min(self.concurrency + self.ADAPTIVE_STEP, self.max_limit)
                log(f"📈 Increasing concurrency to {self.concurrency}")

                # Reset fast completion counter after scaling up
                self.fast_completions = 0  
        else:
            # Reset fast completion count on failure
            self.fast_completions = 0  

            # If concurrency is greater than minimum, decrease it
            if self.concurrency > self.MIN_CONCURRENCY:
                self.concurrency = max(self.concurrency - self.ADAPTIVE_STEP, self.MIN_CONCURRENCY)
                log(f"📉 Decreasing concurrency to {self.concurrency}")
    
    def get_concurrency(self):
        return self.concurrency

