import asyncio
import sys
import logging
import datetime
from multidict import MultiDict
from weakref import WeakValueDictionary

import aiohttp

from . import __version__
from .exception import TwitchException

log = logging.getLogger(__name__)


class LockHelper:
    def __init__(self, lock):
        self.lock = lock
        self._unlock = True

    def __enter__(self):
        return self

    def defer(self):
        self._unlock = False

    def __exit__(self, type, value, traceback):
        if self._unlock:
            self.lock.release()


class HTTPException(TwitchException):
    def __init__(self, response, error, status=None):
        self.status = response.status if not status else status
        self.response = response
        self.message = None
        if isinstance(error, dict):
            self.message = error.get('message', 'Unknown')
            self.error = error.get('error', '')
        else:
            self.error = error

        reason = f' (reason: {self.message})' if self.message else ''
        e = f'{self.status} {self.error}{reason}'
        super().__init__(e)


class HTTPNotAuthorized(HTTPException):
    def __init__(self, response, error):
        super().__init__(response, error, 401)


class HTTPForbidden(HTTPException):
    def __init__(self, response, error):
        super().__init__(response, error, 403)


class HTTPNotFound(HTTPException):
    def __init__(self, response, error):
        super().__init__(response, error, 404)


class HTTPRoute:
    BASE_URL = 'https://api.twitch.tv/helix'

    def __init__(self, method, path):
        self.method = method
        self.path = path
        self.url = self.BASE_URL + self.path

    @property
    def bucket(self):
        return f'{self.method}:{self.path}'


class HTTPClient:
    RETRY_LIMIT = 10
    TOKEN_PREFIX = 'oauth:'

    def __init__(self, connector=None, loop=None):
        self.loop = loop if loop else asyncio.get_event_loop()
        self.connector = connector
        self._access_token = None
        self._session = None
        self._bucket_locks = WeakValueDictionary()
        self._rate_limit_reset = None

        py_version = '{1[0]}.{1[1]}'.format(__version__, sys.version_info)
        user_agent = f'TwitchBot (https://github.com/sedruk/twitch.py ' \
                     f'{__version__})' \
                     f'Python/{py_version} aiohttp/{aiohttp.__version__}'
        self.user_agent = user_agent

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    async def access_token(self, new_token):
        await self.create_session(new_token)

    async def create_session(self, access_token):
        access_token = HTTPClient._normalize_access_token(access_token)
        self._session = aiohttp.ClientSession(connector=self.connector,
                                              loop=self.loop)
        previous_token = self._access_token
        self._access_token = access_token

        try:
            await self.request(HTTPRoute('GET', '/games'), params={'id': 0})
        except HTTPException as e:
            self._access_token = previous_token
            if e.status == 401:
                raise HTTPNotAuthorized(e.response,
                                        'invalid/expired access token '
                                        'has been passed')
            raise

    def recreate_session(self):
        if self._session and self._session.closed:
            self._session = aiohttp.ClientSession(connector=self.connector,
                                                  loop=self.loop)

    async def close_session(self):
        if self._session:
            await self._session.close()

    @staticmethod
    def _normalize_access_token(access_token):
        # ensure the token doesn't have the prefix that
        # https://twitchapps.com/tmi/ automatically prepends.
        # this is a common place for people to get their access tokens
        # from so its good to handle this for users
        return access_token.lstrip(HTTPClient.TOKEN_PREFIX)

    @staticmethod
    def _get_ratelimit_reset(reset_epoch):
        utc = datetime.timezone.utc
        now = datetime.datetime.now(utc)
        reset = datetime.datetime.fromtimestamp(reset_epoch, utc)
        return (reset - now).total_seconds()

    def _handle_ratelimit(self, bucket, headers, status):
        if 'ratelimit-remaining' in headers and 'ratelimit-reset' in headers:
            if headers['ratelimit-remaining'] == str(0) and status != 429:
                reset_epoch = int(headers['ratelimit-reset'])
                reset_seconds = HTTPClient._get_ratelimit_reset(reset_epoch)
                self._rate_limit_reset = reset_seconds
                return reset_seconds
        return None

    async def request(self, route, **kwargs):
        bucket = route.bucket
        method = route.method
        url = route.url

        lock = self._bucket_locks.get(bucket)
        if not lock:
            lock = asyncio.Lock(loop=self.loop)
            if bucket is not None:
                self._bucket_locks[bucket] = lock

        headers = {'User-Agent': self.user_agent}

        if self._access_token is not None:
            headers['Authorization'] = f'Bearer {self._access_token}'
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = kwargs.pop('json')
        else:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        kwargs['headers'] = headers

        await lock.acquire()
        with LockHelper(lock) as lock_helper:
            for attempt in range(HTTPClient.RETRY_LIMIT):
                async with self._session.request(method, url,
                                                 **kwargs) as response:
                    log.info(
                        f'request to {method} {url} with {kwargs.get("data")} '
                        f'returned {response.status}')

                    data = await response.json()

                    reset_seconds = self._handle_ratelimit(bucket,
                                                           response.headers,
                                                           response.status)
                    if reset_seconds:
                        log.info(
                            f'bucket {bucket} rate limit has been exhausted. '
                            f'Retrying in {reset_seconds} seconds')
                        lock_helper.defer()
                        self.loop.call_later(reset_seconds, lock.release)

                    if 200 <= response.status < 300:
                        self._rate_limit_reset = None
                        return data

                    if response.status == 429:
                        # from https://dev.twitch.tv/docs/api/guide
                        # 'Rate Limit' section. there it states the refill
                        # rate is per minute, since the API doesn't provide
                        # us with when we should retry, im just
                        # picking a reasonable value that will allow some
                        # points to be re-filled
                        arbitrary_retry = 5
                        msg = f'the client is being rate limited. Bucket ' \
                              f'{bucket} rate limit has been exceeded. ' \
                              f'retrying in {arbitrary_retry} seconds'
                        log.warning(msg)

                        await asyncio.sleep(arbitrary_retry, loop=self.loop)
                        log.info(
                            f'sleep complete for the rate limited bucket '
                            f'{bucket}. Retrying...')

                        continue

                    if response.status in (500, 502):
                        retry = 1 + attempt * 2
                        log.info(
                            f'server side error, retrying in {retry} seconds')
                        await asyncio.sleep(retry, loop=self.loop)
                        continue

                    if response.status == 401:
                        raise HTTPNotAuthorized(response, data)
                    elif response.status == 403:
                        raise HTTPForbidden(response, data)
                    elif response.status == 404:
                        raise HTTPNotFound(response, data)
                    else:
                        raise HTTPException(response, data)

            log.info(
                f'request to {method} {url} with {kwargs.get("data")} was '
                f'attempted {HTTPClient.RETRY_LIMIT} times without success')
            raise HTTPException(response, data)

    # analytics

    def get_extension_analytics(self, *, after=None, ended_at=None,
                                extension_id=None, first=None, started_at=None,
                                analystics_type=None):
        route = HTTPRoute('GET', '/analytics/extensions')
        params = {}
        if after:
            params['after'] = after
        if ended_at:
            params['ended_at'] = ended_at
        if extension_id:
            params['extension_id'] = extension_id
        if first:
            params['first'] = first
        if started_at:
            params['started_at'] = started_at
        if analystics_type:
            params['type'] = analystics_type
        return self.request(route, params=params)

    def get_game_analytics(self, *, after=None, ended_at=None, first=None,
                           game_id=None, started_at=None,
                           analystics_type=None):
        route = HTTPRoute('GET', '/analytics/games')
        params = {}
        if after:
            params['after'] = after
        if ended_at:
            params['ended_at'] = ended_at
        if game_id:
            params['game_id'] = game_id
        if first:
            params['first'] = first
        if started_at:
            params['started_at'] = started_at
        if analystics_type:
            params['type'] = analystics_type
        return self.request(route, params=params)

    # bits

    def get_bits_leaderboard(self, *, count=None, period=None, started_at=None,
                             user_id=None):
        route = HTTPRoute('GET', '/bits/leaderboard')
        params = {}
        if count:
            params['count'] = count
        if period:
            params['period'] = period
        if started_at:
            params['started_at'] = started_at
        if user_id:
            params['user_id'] = user_id
        return self.request(route, params=params)

    # extensions

    def get_extension_transactions(self, *, extension_id, transaction_id=None,
                                   after=None, first=None):
        route = HTTPRoute('GET', '/extensions/transactions')
        params = {'extension_id': extension_id}
        if transaction_id:
            params['id'] = transaction_id
        if after:
            params['after'] = after
        if first:
            params['first'] = first
        return self.request(route, params=params)

    # clips

    def create_clip(self, *, broadcaster_id, has_delay=None):
        route = HTTPRoute('POST', '/clips')
        params = {'broadcaster_id': broadcaster_id}
        if has_delay:
            params['has_delay'] = has_delay
        return self.request(route, params=params)

    def get_clips(self, broadcaster_id=None, game_id=None, clip_id=None, *,
                  after=None, before=None, ended_at=None,
                  first=None, started_at=None):
        route = HTTPRoute('GET', '/clips')
        params = {}
        if broadcaster_id:
            params['broadcaster_id'] = broadcaster_id
        if game_id:
            params['game_id'] = game_id
        if clip_id:
            params['id'] = clip_id
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if ended_at:
            params['ended_at'] = ended_at
        if first:
            params['first'] = first
        if started_at:
            params['started_at'] = started_at
        return self.request(route, params=params)

    # entitlements

    def create_entitlement_grants_upload_url(self, *, manifest_id,
                                             entitlement_type):
        route = HTTPRoute('POST', '/entitlements/upload')
        params = {'manifest_id': manifest_id, 'type': entitlement_type}
        return self.request(route, params=params)

    def get_code_status(self, *, code, user_id):
        route = HTTPRoute('GET', '/entitlements/codes')
        params = {'code': code, 'user_id': user_id}
        return self.request(route, params=params)

    def reedem_code(self, *, code, user_id):
        route = HTTPRoute('POST', '/entitlements/code')
        params = {'code': code, 'user_id': user_id}
        return self.request(route, params=params)

    # games

    def get_top_games(self, *, after=None, before=None, first=None):
        route = HTTPRoute('GET', '/games/top')
        params = {}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if first:
            params['first'] = first
        return self.request(route, params=params)

    def get_games(self, *, game_id=None, name=None):
        route = HTTPRoute('GET', '/games')
        params = {}
        if game_id:
            params['id'] = game_id
        if name:
            params['name'] = name
        return self.request(route, params=params)

    # moderation

    def check_automod_status(self, *, broadcaster_id, messages):
        route = HTTPRoute('POST', '/moderation/enforcements/status')
        params = {'broadcaster_id': broadcaster_id}
        json = {}
        json['data'] = [
            {'msg_id': msg_id, 'msg_text': msg_text, 'user_id': user_id} for
            (msg_id, msg_text, user_id) in
            messages]
        return self.request(route, params=params, json=json)

    def get_banned_events(self, *, broadcaster_id, user_id=None, after=None,
                          first=None):
        route = HTTPRoute('GET', '/moderation/banned/events')
        params = {'broadcaster_id': broadcaster_id}
        if user_id:
            params['user_id'] = user_id
        if after:
            params['after'] = after
        if first:
            params['first'] = first
        return self.request(route, params=params)

    def get_banned_users(self, *, broadcaster_id, user_id=None, after=None,
                         first=None):
        route = HTTPRoute('GET', '/moderation/banned')
        params = {'broadcaster_id': broadcaster_id}
        if user_id:
            params['user_id'] = user_id
        if after:
            params['after'] = after
        if first:
            params['first'] = first
        return self.request(route, params=params)

    def get_moderators(self, *, broadcaster_id, user_id=None, after=None):
        route = HTTPRoute('GET', '/moderation/moderators')
        params = {'broadcaster_id': broadcaster_id}
        if user_id:
            params['user_id'] = user_id
        if after:
            params['after'] = after
        return self.request(route, params=params)

    def get_moderator_events(self, *, broadcaster_id, user_id=None):
        route = HTTPRoute('GET', '/moderation/moderators/events')
        params = {'broadcaster_id': broadcaster_id}
        if user_id:
            params['user_id'] = user_id
        return self.request(route, params=params)

    # subscriptions

    def get_broadcaster_subscriptions(self, *, broadcaster_id, user_id=None):
        route = HTTPRoute('GET', '/subscriptions')
        params = {'broadcaster_id': broadcaster_id}
        if user_id:
            params['user_id'] = user_id
        return self.request(route, params=params)

    # streams

    def get_streams(self, *, after=None, before=None, first=None, game_id=None,
                    language=None, user_id=None,
                    user_login=None):
        route = HTTPRoute('GET', '/streams')
        params = {}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if first:
            params['first'] = first
        if game_id:
            params['game_id'] = game_id
        if language:
            params['language'] = language
        if user_id:
            params['user_id'] = user_id
        if user_login:
            params['user_login'] = user_login
        return self.request(route, params=params)

    # stream metadata

    def get_streams_metadata(self, *, after=None, before=None, first=None,
                             game_id=None, language=None, user_id=None,
                             user_login=None):
        route = HTTPRoute('GET', '/streams/metadata')
        params = {}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if first:
            params['first'] = first
        if game_id:
            params['game_id'] = game_id
        if language:
            params['language'] = language
        if user_id:
            params['user_id'] = user_id
        if user_login:
            params['user_login'] = user_login
        return self.request(route, params=params)

    # stream markers

    def create_stream_marker(self, *, user_id, description=None):
        route = HTTPRoute('POST', '/streams/markers')
        json = {'user_id': user_id}
        if description:
            json['description'] = description
        return self.request(route, json=json)

    def get_stream_markers(self, *, user_id, video_id, after=None, before=None,
                           first=None):
        route = HTTPRoute('GET', '/streams/markers')
        params = {'user_id': user_id, 'video_id': video_id}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if first:
            params['first'] = first
        return self.request(route, params=params)

    # stream tags

    def get_all_stream_tags(self, *, after=None, first=None, tag_id=None):
        route = HTTPRoute('GET', '/streams/tags')
        params = {}
        if after:
            params['after'] = after
        if first:
            params['first'] = first
        if tag_id:
            params['tag_id'] = tag_id
        return self.request(route, params=params)

    def get_stream_tags(self, *, broadcaster_id):
        route = HTTPRoute('GET', '/streams/tags')
        params = {'broadcaster_id': broadcaster_id}
        return self.request(route, params=params)

    def replace_stream_tags(self, *, broadcaster_id, tag_ids=None):
        route = HTTPRoute('PUT', '/streams/tags')
        params = {'broadcaster_id': broadcaster_id}
        json = {}
        if tag_ids:
            json['tag_ids'] = tag_ids
        return self.request(route, params=params, json=json)

    # users

    def get_users(self, *, user_ids=None, logins=None):
        route = HTTPRoute('GET', '/users')
        params = MultiDict()
        if user_ids:
            for user_id in user_ids:
                params.add('id', user_id)
        if logins:
            for login in logins:
                params.add('login', login)
        return self.request(route, params=params)

    def get_user_follows(self, *, from_id=None, to_id=None, after=None,
                         first=None):
        route = HTTPRoute('GET', '/users/follows')
        params = {}
        if from_id:
            params['from_id'] = from_id
        if to_id:
            params['to_id'] = to_id
        if after:
            params['after'] = after
        if first:
            params['first'] = first
        return self.request(route, params=params)

    def update_user(self, *, description=None):
        route = HTTPRoute('PUT', '/users')
        params = {}
        if description:
            params['description'] = description
        return self.request(route, params=params)

    # user extensions

    def get_user_extensions(self):
        return self.request(HTTPRoute('GET', '/users/extensions/list'))

    def get_user_active_extensions(self, *, user_id=None):
        route = HTTPRoute('GET', '/users/extensions')
        params = {}
        if user_id:
            params['user_id'] = user_id
        return self.request(route, params=params)

    def update_user_extensions(self, *, panels=None, components=None,
                               overlays=None):
        route = HTTPRoute('PUT', '/users/extensions')
        json = {'data': {}}

        def inc(i):
            return i + 1

        json['data']['panel'] = [
            {inc(i): {'active': tup[0], 'id': tup[1], 'version': tup[2]}} for
            i, tup in
            list(enumerate(panels))
        ]

        json['data']['component'] = [
            {inc(i): {'active': tup[0], 'id': tup[1], 'version': tup[2],
                      'x': tup[3], 'y': tup[4]}} for i, tup in
            list(enumerate(components))
        ]

        json['data']['overlay'] = [
            {inc(i): {'active': tup[0], 'id': tup[1], 'version': tup[2]}} for
            i, tup in
            list(enumerate(overlays))
        ]

        return self.request(route, json=json)

    # videos

    def get_videos(self, *, video_id, user_id, game_id, after=None,
                   before=None, first=None, language=None, period=None,
                   sort=None, video_type=None):
        route = HTTPRoute('GET', '/videos')
        params = {'id': video_id, 'user_id': user_id, 'game_id': game_id}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if first:
            params['first'] = first
        if language:
            params['language'] = language
        if period:
            params['period'] = period
        if sort:
            params['sort'] = sort
        if video_type:
            params['type'] = video_type
        return self.request(route, params=params)

    # webhooks

    def get_webhook_subscriptions(self, *, after=None, first=None):
        route = HTTPRoute('GET', '/webhooks/subscriptions')
        params = {}
        if after:
            params['after'] = after
        if first:
            params['first'] = first
        return self.request(route, params=params)

    def create_webhook(self, *, hub_callback, hub_mode, hub_topic,
                       hub_lease_seconds=None, hub_secret=None):
        route = HTTPRoute('POST', '/webhooks/hub')
        json = {'hub.callback': hub_callback, 'hub.mode': hub_mode,
                'hub.topic': hub_topic}
        if hub_lease_seconds:
            json['hub.lease_seconds'] = hub_lease_seconds
        if hub_secret:
            json['hub.secret'] = hub_secret
        return self.request(route, json=json)
