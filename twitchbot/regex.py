import re

RE_PRIVMSG = re.compile(
    r'(?P<tags>.*):'
    r'(?P<user>[\w\d]+)!(?P=user)@(?P=user)\.tmi\.twitch\.tv PRIVMSG #(?P<channel>[\w\d]+) :(?P<content>.+)'
)

# example whisper
# :nickname!nickname@nickname.tmi.twitch.tv WHISPER bob :hello world!
RE_WHISPER = re.compile(
    r':(?P<user>[\w\d]+)!(?P=user)@(?P=user)\.tmi\.twitch\.tv WHISPER (?P<receiver>[\w\d]+) :(?P<content>.+)'
)

# example joining channel
# :nickname!nickname@nickname.tmi.twitch.tv JOIN #bob
RE_USER_JOIN = re.compile(
    r':(?P<user>[\w\d]+)!(?P=user)@(?P=user)\.tmi\.twitch\.tv JOIN #(?P<channel>\w+)'
)

# user leaves the channel
#  :nickname!nickname@nickname.tmi.twitch.tv PART #bob
RE_USER_PART = re.compile(
    r':(?P<user>[\w\d]+)!(?P=user)@(?P=user)\.tmi\.twitch\.tv PART #(?P<channel>\w+)'
)

# finds mentions in twitch messages
# example: hello @bob!
RE_AT_MENTION = re.compile(
    r'@([\w\d]+)'
)

# user notices / subscriptions
RE_USERNOTICE = re.compile(
    r'(?P<tags>.*):tmi\.twitch\.tv USERNOTICE #(?P<channel>[\w\d]+)(?: :)?(?P<content>.+)?'
)

# user notices / subscriptions
# example:
# @msg-id=msg_banned :tmi.twitch.tv NOTICE #X :You are permanently banned from talking in X.
RE_NOTICE = re.compile(
    r'(?P<tags>.*):tmi\.twitch\.tv NOTICE #(?P<channel>[\w\d]+)(?: :)?(?P<content>.+)?'
)

#  @msg-id=msg_timedout :tmi.twitch.tv NOTICE #X :You are timed out for 99906 more seconds.
RE_TIMEOUT_DURATION = re.compile(
    r'timed out for (?P<seconds>\d+)'
)

#    @badge-info=;badges=moderator/1;color=#9ACD32;display-name=HammerheadB0t;emote-sets=0,300374282;mod=1;subscriber=0;user-type=mod :tmi.twitch.tv USERSTATE #userman2
RE_USER_STATE = re.compile(
    r'(?P<tags>.*?):tmi\.twitch\.tv USERSTATE #(?P<channel>[\w\d]+)'
)

#    @emote-only=0;followers-only=-1;r9k=0;room-id=35927458;slow=0;subs-only=0 :tmi.twitch.tv ROOMSTATE #userman2
RE_ROOM_STATE = re.compile(
    r'(?P<tags>.*?):tmi\.twitch\.tv ROOMSTATE #(?P<channel>[\w\d]+)'
)
