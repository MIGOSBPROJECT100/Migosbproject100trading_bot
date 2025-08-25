from datetime import timedelta

FOOTER_SUFFIX = "\n\n_Managed by @bank_rats | @Migos_B_Fx254_"

NEWS_LOCK_WINDOW_MINUTES = 30  # ±30 lock
FEEDBACK_COOLDOWN_SECONDS = 60

FREE_TIER_DAILY_SIGNAL_LIMIT = 1

# Admin denial
ADMIN_DENIAL = (
    "This action is denied. The requested command is for admin use only. "
    "For assistance, please contact @bank_rats or @Migos_B_Fx254."
) + FOOTER_SUFFIX
