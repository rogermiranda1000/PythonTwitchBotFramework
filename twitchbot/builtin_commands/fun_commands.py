from secrets import choice
from random import randint

from twitchbot import (
    Message,
    CommandContext,
    Command,
    InvalidArgumentsError,
    translate,
)


@Command('roll', context=CommandContext.BOTH, syntax='(sides)', help='rolls a X sided die')
async def cmd_roll(msg: Message, *args):
    try:
        sides = int(args[0]) if args else 6
    except ValueError:
        raise InvalidArgumentsError(reason=translate('roll_invalid_sides'), cmd=cmd_roll)

    num = randint(1, sides)
    user = msg.mention if msg.is_privmsg else ''
    await msg.reply(translate('roll_result', user=user, num=num))


@Command('crashcode', permission='crashcode')
async def cmd_crash_code(msg: Message, *args):
    await msg.reply(translate('crashme', mention=msg.mention))


@Command('choose', syntax='<option> <option> ect', help='chooses a random option passed to the command')
async def cmd_choose(msg: Message, *args):
    if len(args) < 2:
        raise InvalidArgumentsError(reason=translate('missing_required_arguments'), cmd=cmd_choose)

    await msg.reply(translate('choose_result', value=choice(args)))


@Command('color', permission='color', syntax='<color>', help='sets the bots chat color')
async def cmd_color(msg: Message, *args):
    if not args:
        raise InvalidArgumentsError(reason=translate('missing_required_arguments'), cmd=cmd_color)

    await msg.channel.color(args[0])
    await msg.reply(translate('color_set', color=args[0]))


magic_8_ball_messages = [
    '8ball_yes_1',
    '8ball_yes_2',
    '8ball_no_1',
    '8ball_no_2',
    '8ball_maybe_1',
    '8ball_maybe_2',
]


@Command('8ball', syntax='<question>', help='prints a random answer to the question')
async def cmd_8ball(msg: Message, *args):
    await msg.reply(translate('8ball_result', mention=msg.mention, value=translate(choice(magic_8_ball_messages))))
