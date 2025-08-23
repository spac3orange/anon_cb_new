from aiogram.types import BotCommand


async def set_commands_menu(bot):
    main_menu_commands = [
        BotCommand(command='/search',
                   description='Поиск собеседника'),
        BotCommand(command='/stop',
                   description='Остановить диалог')
        ]

    await bot.set_my_commands(main_menu_commands)
