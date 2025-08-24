import logging
from telegram.ext import Application
from config import TELEGRAM_BOT_TOKEN
from services.command_handler import setup_handlers

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    logger.info("Bot is starting...")
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Setup all handlers from the command_handler module
    setup_handlers(application)

    # Log all errors
    async def error_handler(update: object, context) -> None:
        logger.warning(f'Update "{update}" caused error "{context.error}"')
    
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
