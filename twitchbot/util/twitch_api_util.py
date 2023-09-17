import warnings

from typing import Dict, Tuple, NamedTuple, Optional, Any
from collections import namedtuple
from datetime import datetime
from json import JSONDecodeError, JSONEncoder, dumps as json_dumps

from aiohttp import ClientSession, ClientResponse, ContentTypeError
from async_timeout import timeout

from ..config import get_client_id, get_oauth, get_nick, DEFAULT_CLIENT_ID
from ..data import UserFollowers, UserInfo, Follower

__all__ = ('CHANNEL_CHATTERS_API_URL', 'get_channel_chatters', 'get_stream_data', 'get_url', 'get_user_data', 'get_user_id',
           'STREAM_API_URL', 'USER_API_URL', 'get_user_followers', 'USER_FOLLOWERS_API_URL', 'get_headers',
           'get_user_info', 'USER_ACCOUNT_AGE_API', 'CHANNEL_INFO_API', 'get_channel_info', 'ChannelInfo',
           'get_channel_name_from_user_id', 'OauthTokenInfo', 'get_oauth_token_info', '_check_token', 'post_url', 'USER_FOLLOWAGE_API_URL',
           'get_user_followage', 'send_shoutout', 'send_announcement', 'send_ban', 'delete_url', 'send_unban', 'SendTwitchApiResponseStatus')

USER_API_URL = 'https://api.twitch.tv/helix/users?login={}'
STREAM_API_URL = 'https://api.twitch.tv/helix/streams?user_login={}'
CHANNEL_CHATTERS_API_URL = 'https://api.twitch.tv/helix/chat/chatters?moderator_id={}&broadcaster_id={}'
USER_FOLLOWERS_API_URL = 'https://api.twitch.tv/helix/users/follows?to_id={}'
USER_ACCOUNT_AGE_API = 'https://api.twitch.tv/kraken/users/{}'
CHANNEL_INFO_API = 'https://api.twitch.tv/helix/channels?broadcaster_id={}'
USER_FOLLOWAGE_API_URL = 'https://api.twitch.tv/helix/channels/followers?broadcaster_id={}&user_id={}'
SHOUTOUT_API_URL = 'https://api.twitch.tv/helix/chat/shoutouts?from_broadcaster_id={}&to_broadcaster_id={}&moderator_id={}'
ANNOUNCEMENTS_API_URL = 'https://api.twitch.tv/helix/chat/announcements?broadcaster_id={}&moderator_id={}'
BAN_API_URL = 'https://api.twitch.tv/helix/moderation/bans?broadcaster_id={}&moderator_id={}'
UNBAN_API_URL = 'https://api.twitch.tv/helix/moderation/bans?broadcaster_id={}&moderator_id={}&user_id={}'

user_id_cache: Dict[str, int] = {}


async def get_url(url: str, headers: dict = None) -> Tuple[ClientResponse, dict]:
    headers = headers if headers is not None else get_headers()
    async with ClientSession(headers=headers) as session:
        async with timeout(10):
            async with session.get(url) as resp:
                return await _extract_response_and_json_from_request(resp)


async def post_url(url: str, headers: dict = None, body: Any = None) -> Tuple[ClientResponse, dict]:
    headers = headers if headers is not None else get_headers()
    async with ClientSession(headers=headers) as session:
        async with timeout(10):
            async with session.post(url, data=body) as resp:
                return await _extract_response_and_json_from_request(resp)


async def delete_url(url: str, headers: dict = None) -> Tuple[ClientResponse, dict]:
    headers = headers if headers is not None else get_headers()
    async with ClientSession(headers=headers) as session:
        async with timeout(10):
            async with session.delete(url) as resp:
                return await _extract_response_and_json_from_request(resp)


def _check_headers_has_auth(headers: dict) -> bool:
    return CLIENT_ID_KEY in headers and AUTHORIZATION_KEY in headers


async def _extract_response_and_json_from_request(resp):
    try:
        return resp, await resp.json()
    except (ContentTypeError, JSONDecodeError, TypeError):
        return resp, {}


async def get_user_info(user: str) -> UserInfo:
    headers = get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_USER_INFO] headers for the twitch api request are missing authorization', stacklevel=2)
        return UserInfo(-1, '', '', '', '', '', '', '', -1)

    _, json = await get_url(USER_API_URL.format(user), headers)

    if 'error' in json or not json.get('data', None):
        return UserInfo(-1, '', '', '', '', '', '', '', -1)

    data = json['data'][0]
    return UserInfo(
        id=int(data['id']),
        login=data['login'],
        display_name=data['display_name'],
        type=data['type'],
        broadcaster_type=data['broadcaster_type'],
        description=data['description'],
        profile_image_url=data['profile_image_url'],
        offline_image_url=data['offline_image_url'],
        view_count=data['view_count']
    )


async def get_user_followers(user: str, headers: dict = None) -> UserFollowers:
    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_USER_FOLLOWERS] headers for the twitch api request are missing authorization', stacklevel=2)
        return UserFollowers(-1, '', -1, '', -1, [])

    user_id = await get_user_id(user, headers)
    _, json = await get_url(USER_FOLLOWERS_API_URL.format(user_id), headers)

    # covers invalid user id, or some other API error, such as invalid client-id
    if not json or json.get('status', -1) == 400:
        return UserFollowers(-1, '', -1, '', -1, [])

    return UserFollowers(follower_count=json['total'],
                         following=user,
                         following_id=user_id,
                         name=user,
                         id=user_id_cache[user],
                         followers=json['data'])


async def get_user_followage(channel_name: str, follower: str, headers: dict = None) -> Follower:
    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_USER_FOLLOWAGE] headers for the twitch api request are missing authorization', stacklevel=2)
        return Follower(-1, '', -1, '', datetime.min)

    channel_id = await get_user_id(channel_name, headers)
    follower_id = await get_user_id(follower, headers)
    _, json = await get_url(USER_FOLLOWAGE_API_URL.format(channel_id, follower_id), headers)

    # verify that the api response has data, and its total is not 0
    if not json or not json.get('total', 0) or not json.get('data'):
        return Follower(-1, '', -1, '', datetime.min)

    # todo: test this out properly
    return Follower(following=channel_name,
                    following_id=channel_id,
                    id=follower_id,
                    name=json['data'][0]['user_name'],
                    # datetime format: 2019-10-23T23:12:06Z
                    followed_at=datetime.fromisoformat(json['data'][0]['followed_at'][:-1]))


class SendTwitchApiResponseStatus(NamedTuple):
    success: bool
    status_code: int
    resp: ClientResponse
    text: str
    json: dict

    async def json(self) -> dict:
        return await self.resp.json()


async def send_shoutout(channel_name: str, target_name: str, headers: dict = None) -> SendTwitchApiResponseStatus:
    headers = (headers.copy() if headers is not None else get_headers())
    if not _check_headers_has_auth(headers):
        warnings.warn('[SHOUTOUT] headers for the twitch api request are missing authorization', stacklevel=2)

    channel_id = await get_user_id(channel_name, headers)
    target_id = await get_user_id(target_name, headers)
    moderator_id = await get_user_id(get_nick(), headers)

    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    resp, json = await enqueue_twitch_api_request(
        SHOUTOUT_API_URL.format(channel_id, target_id, moderator_id),
        headers=headers,
        mode=PendingTwitchAPIRequestMode.POST
    )

    if (resp.status != 204):
        resp_text = await resp.text("utf-8")
        warnings.warn(
            f'Shoutout failed with error code: {resp.status}.\nResponse: {resp_text}\nSee "https://dev.twitch.tv/docs/api/reference/#send-a-shoutout"',
            stacklevel=2)

    return SendTwitchApiResponseStatus(
        success=resp.status == 204,
        status_code=resp.status,
        resp=resp,
        text=await resp.text("utf-8"),
        json=json
    )


async def send_announcement(channel_name: str, message: str, color: str = None, headers: dict = None) -> SendTwitchApiResponseStatus:
    headers = headers.copy() if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[ANNOUNCEMENT] headers for the twitch api request are missing authorization', stacklevel=2)

    channel_id = await get_user_id(channel_name, headers)
    moderator_id = await get_user_id(get_nick(), headers)

    if len(message) > 500:
        warnings.warn(f'Announcements messages above 500 Characters are trunscated by Twitch. Given length is {len(message)}', stacklevel=2)

    if color not in {'blue', 'green', 'orange', 'purple'}:
        warnings.warn(f'Announcements color can only be blue, green, orange or purple. Given color is {color} defaulting to primary', stacklevel=2)
        color = 'primary'

    body = json_dumps({'message': message, 'color': color})

    headers.update({'Content-Type': 'application/json'})
    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    resp, json = await enqueue_twitch_api_request(
        ANNOUNCEMENTS_API_URL.format(channel_id, moderator_id),
        headers=headers,
        body=body,
        mode=PendingTwitchAPIRequestMode.POST
    )

    if (resp.status != 204):
        resp_text = await resp.text("utf-8")
        warnings.warn(
            f'Announcement failed with error code: {resp.status}.\nResponse Text: {resp_text}.\nSee "https://dev.twitch.tv/docs/api/reference/#send-chat-announcement"',
            stacklevel=2)

    return SendTwitchApiResponseStatus(
        success=resp.status == 204,
        status_code=resp.status,
        resp=resp,
        text=await resp.text(),
        json=json
    )


async def send_unban(channel_name: str, username: str, headers: dict = None) -> SendTwitchApiResponseStatus:
    headers = headers.copy() if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[UNBAN] headers for the twitch api request are missing authorization', stacklevel=2)

    moderator_id = await get_user_id(get_nick(), headers)
    broadcaster_id = await get_user_id(channel_name, headers)
    user_id = await get_user_id(username, headers)
    #                                                broadcaster_id={}&moderator_id={}&user_id={}
    resp, json = await delete_url(UNBAN_API_URL.format(broadcaster_id, moderator_id, user_id))

    if resp.status != 204:
        resp_text = await resp.text()
        warnings.warn(
            f'[UNBAN] Unban failed with error code: {resp.status}.\nResponse Text: {resp_text}.\nSee "https://dev.twitch.tv/docs/api/reference/#unban-user"',
            stacklevel=2)

    return SendTwitchApiResponseStatus(
        success=resp.status == 204,
        status_code=resp.status,
        resp=resp,
        text=await resp.text(),
        json=json,
    )


async def send_ban(
        channel_name: str, username: str, reason: str = None, timeout: int = None, headers: dict = None
) -> Optional[SendTwitchApiResponseStatus]:
    headers = headers.copy() if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[BAN] headers for the twitch api request are missing authorization', stacklevel=2)

    channel_id = await get_user_id(channel_name, headers)
    user_id = await get_user_id(username, headers)
    moderator_id = await get_user_id(get_nick(), headers)

    if reason is None:
        reason = ''

    if len(reason) > 500:
        reason = reason[:500]
        warnings.warn(f'[BAN] reasons above 500 Characters is limited by Twitch and will be truncated. Given length is {len(reason)}.', stacklevel=2)

    # Split it into two If-statements for better understanding
    if timeout is not None:
        # Just for safety
        if not isinstance(timeout, int):
            warnings.warn(f'[BAN] timeout need to be of type integer. Given type is {type(timeout)}. ABORTING!', stacklevel=2)
            return None

        elif not 1 <= timeout <= 1209600:
            warnings.warn(f'[BAN] timeout needs to be between 1 or 1209600 Seconds (2 Weeks). Given timout is {timeout}, setting to 600 Seconds.',
                          stacklevel=2)
            timeout = 600

        body = json_dumps({'data': {'user_id': user_id, 'duration': timeout, 'reason': reason}})
    else:
        # Permanent Ban
        body = json_dumps({'data': {'user_id': user_id, 'reason': reason}})

    headers.update({'Content-Type': 'application/json'})
    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    resp, json = await enqueue_twitch_api_request(
        BAN_API_URL.format(channel_id, moderator_id),
        headers=headers,
        body=body,
        mode=PendingTwitchAPIRequestMode.POST
    )

    if resp is not None and resp.status != 200:
        returnMessage = json['message']
        warnings.warn(
            f'Ban failed with error code: {resp.status}, with message "{returnMessage}". See "https://dev.twitch.tv/docs/api/reference/#ban-user"',
            stacklevel=2)

    return SendTwitchApiResponseStatus(
        success=resp is not None and resp.status == 200,
        status_code=resp.status,
        resp=resp,
        text=await resp.text(),
        json=json
    )


async def get_user_data(user: str, headers: dict = None) -> dict:
    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_USER_DATA] headers for the twitch api request are missing authorization', stacklevel=2)
        return {}

    # _, json = await get_url(USER_API_URL.format(user), headers)
    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    _, json = await enqueue_twitch_api_request(USER_API_URL.format(user), headers, PendingTwitchAPIRequestMode.GET)

    if not json.get('data'):
        return {}

    return json['data'][0]


async def get_user_id(user: str, headers: dict = None, verbose=True) -> int:
    # shortcut if the user's id was already requested
    if user in user_id_cache:
        return user_id_cache[user]

    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_USER_DATA] headers for the twitch api request are missing authorization', stacklevel=2)
        return -1

    data = await get_user_data(user, headers)

    if not data:
        if verbose:
            warnings.warn(f'[GET_USER_ID] unable to get user_id for username "{user}"', stacklevel=2)
        return -1

    user_id_cache[user] = data['id']
    return data['id']


async def get_stream_data(user_id: str, headers: dict = None) -> dict:
    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_STREAM_DATA] headers for the twitch api request are missing authorization', stacklevel=2)
        return {}
    
    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    _, json = await enqueue_twitch_api_request(STREAM_API_URL.format(user_id), headers, PendingTwitchAPIRequestMode.GET)

    if not json.get('data'):
        return {}

    return json['data'][0]


async def get_channel_chatters(channel: str, headers: dict = None) -> dict:
    headers = headers.copy() if headers is not None else get_headers()

    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_CHANNEL_CHATTERS] headers for the twitch api request are missing authorization', stacklevel=2)
        return {}

    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    resp, data = await enqueue_twitch_api_request(
        CHANNEL_CHATTERS_API_URL.format(await get_user_id(get_nick(), headers), await get_user_id(channel, headers)), headers,
        PendingTwitchAPIRequestMode.GET
    )

    if resp.status == 403:
        print(f'[GET_CHANNEL_CHATTERS] Failed to get channel chatters for channel "{channel}"; Twitch responded with 403 (Forbidden).\n\t'
              f'Make sure that provided token has the scope access `moderator:read:chatters` for channel "{channel}"')
        return {}

    if resp.status != 200 or data.get('error') is not None:
        return {}

    return data


CLIENT_ID_KEY = 'Client-ID'
AUTHORIZATION_KEY = 'Authorization'


def get_headers(use_kraken: bool = False):
    prefix = 'Bearer' if not use_kraken else 'OAuth'
    oauth_key = get_oauth(remove_prefix=True)
    headers = {CLIENT_ID_KEY: get_client_id()}
    if oauth_key:
        headers.update({AUTHORIZATION_KEY: f'{prefix} {oauth_key}'})

    return headers


ChannelInfo = NamedTuple(
    'ChannelInfo', (
        ('broadcaster_id', str),
        ('broadcaster_name', str),
        ('broadcaster_language', str),
        ('game_id', str),
        ('game_name', str),
        ('title', str))
)


async def get_channel_info(broadcaster_name_or_id: str, headers: dict = None) -> Optional[ChannelInfo]:
    from ..util import dict_get_value

    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_CHANNEL_INFO] headers for the twitch api request are missing authorization', stacklevel=2)
        return None

    if not broadcaster_name_or_id.strip().isnumeric():
        user_id = await get_user_id(broadcaster_name_or_id, headers=headers)
        if user_id == -1:
            return None
    else:
        user_id = broadcaster_name_or_id
        
    from ..ratelimit_twitch_api_queue import enqueue_twitch_api_request, PendingTwitchAPIRequestMode
    _, json =  await enqueue_twitch_api_request(CHANNEL_INFO_API.format(user_id), headers, PendingTwitchAPIRequestMode.GET)
    data = dict_get_value(json, 'data', 0)

    if not data:
        return None

    return ChannelInfo(broadcaster_id=data['broadcaster_id'], broadcaster_name=data['broadcaster_name'],
                       broadcaster_language=data['broadcaster_language'], game_id=data['game_id'], game_name=data['game_name'], title=data['title'])


_channel_id_to_name_cache = {}


async def get_channel_name_from_user_id(user_id: str, headers: dict = None) -> str:
    user_id = user_id.strip()

    if user_id in _channel_id_to_name_cache:
        return _channel_id_to_name_cache[user_id]

    headers = headers if headers is not None else get_headers()
    if not _check_headers_has_auth(headers):
        warnings.warn('[GET_CHANNEL_NAME_FROM_USER_ID] headers for the twitch api request are missing authorization', stacklevel=2)
        return ''

    channel_info = await get_channel_info(user_id, headers=headers)

    if not channel_info:
        return ''

    _channel_id_to_name_cache[user_id] = channel_info.broadcaster_name
    return channel_info.broadcaster_name


OauthTokenInfo = namedtuple('OauthTokenInfo', 'client_id login scopes user_id expires_in error_message status')


async def get_oauth_token_info(token: str) -> OauthTokenInfo:
    token = token.replace('oauth:', '')
    _, json = await get_url('https://id.twitch.tv/oauth2/validate', headers={'Authorization': f'OAuth {token}'})
    return OauthTokenInfo(client_id=json.get('client_id', ''),
                          login=json.get('login', ''),
                          scopes=json.get('scopes', []),
                          user_id=json.get('user_id', ''),
                          expires_in=json.get('expires_in', 0),
                          error_message=json.get('message', ''),
                          status=json.get('status', -1))


def _print_quit(msg):
    print(msg)
    input('\npress ENTER to exit...')
    exit(1)


def _check_token(info: OauthTokenInfo):
    if not info.login or info.status != -1:
        _print_quit(f'\nfailed to login to chat, irc oauth token is INVALID/EXPIRED ("oauth" in the config)\n'
                    f'twitch returned status code ({info.status}) and error message ({info.error_message})')

    if get_client_id() != DEFAULT_CLIENT_ID and info.client_id != get_client_id():
        print(f'\n{"=" * 50}\nthe client id for the irc oauth token ("oauth" in the config) DOES NOT match the client id in the config\n'
              f'TWITCH API CALLS WILL NOT WORK until the irc token is regenerated using the client id in the config\n'
              f'\nreplace the <CLIENT_ID_HERE> and <REDIRECT_HERE> in the following auth URL to match your twitch dev app info\nthen visit the URL with '
              f'a browser signed into the bots account to correct this problem\nmake sure to replace the current irc oauth token with the new one ("oauth" in config)'
              f'\n\nhttps://id.twitch.tv/oauth2/authorize?response_type=token&client_id=<CLIENT_ID_HERE>&redirect_uri=<REDIRECT_HERE>'
              f'&scope=chat:read+chat:edit+channel:moderate+whispers:read+whispers:edit+channel_editor'
              f'\n{"=" * 50}\n')

    print(f'logged into chat as "{info.login}"')
