#!/usr/bin/env python3
import requests
from PIL import Image
import numpy as np
from io import BytesIO
import math
import urllib
import argparse
import sys
import os
import time
import re
import copy


def check_args(args=None):
    parser = argparse.ArgumentParser(description="Get an ASCII image from frinkiac. Either search for a quote or get a randome one!", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-r', '--random', help="Get a random quote.", action="store_true")
    parser.add_argument('-q', '--quote', help="Search for a quote.", default="")
    parser.add_argument('-i', '--match_index', help="Index indicating which search result to return. 0-based. Default = '0'.", default="0")
    parser.add_argument('-c', '--caption', help="Custom caption.", default="")
    parser.add_argument('-s', '--season', help="Specify a season. Must be used in conjunction with -e/--episode and -t/--timestamp.", default="")
    parser.add_argument('-e', '--episode', help="Specify an episode. Must be used in conjunction with -s/--season and -t/--timestamp.", default="")
    parser.add_argument('-t', '--timestamp', help="Specify a timestamp. Must be used in conjunction with -s/--season and -e/--episode.", default="")
    parser.add_argument('-T', '--endTimestamp', help="Specify an endpoint timestamp. Must be used in conjunction with -s/--season, -e/--episode, and -t/--timestamp. Only used when using -G/--gif.", default="")
    parser.add_argument('-G', '--gif', help="Specify an animation should be returned with specified length starting from first best match or from specified timestamp of specified episode. Must either specify a duration with -l/--length or an endpoint timestamp with -T/--endTimestamp.", action="store_true")
    parser.add_argument('-l', '--length', help="Specify length (in seconds) of animation to be returned. Only used in conjunction with -G/--gif.", default="")
    parser.add_argument('-I', '--interval', help="Specify the interval between frames, in seconds. Only used in conjunction with -G/--gif. Default = '0.2'.", default="0.2")
    parser.add_argument('-C', '--char', help="Specify a character set (e.g. 0, 1, 2, ...). Use if the default set doesn't work well. Default = '0'.", default="0")
    parser.add_argument('-w', '--width', help="ASCII art width.", default="120")
    parser.add_argument('-g', '--contrast', help="Contrast scaling factor.", default="1")
    parser.add_argument('-p', '--preview', help="Print all quote matches to the screen with relevant information. Only used with -q/--quote.", action="store_true")
    parser.add_argument('-P', '--print_info', help="Print information about the matched frame.", action='store_true')
    arguments = parser.parse_args(args)
    arguments.quote = str(arguments.quote)
    arguments.match_index = int(arguments.match_index)
    if arguments.caption != "":
        arguments.caption = str(arguments.caption)
    if arguments.season != "":
        arguments.season = int(arguments.season)
    if arguments.episode != "":
        arguments.episode = int(arguments.episode)
    if arguments.timestamp != "":
        arguments.timestamp = int(arguments.timestamp)
    if arguments.endTimestamp != "":
        arguments.endTimestamp = int(arguments.endTimestamp)
    if arguments.length != "":
        arguments.length = float(arguments.length)
    arguments.interval = float(arguments.interval)
    arguments.char = int(arguments.char)
    arguments.width = int(arguments.width)
    arguments.contrast = float(arguments.contrast)
    return(arguments)


class Frinky:

    def __init__(self):
        self.random_url = "https://frinkiac.com/api/random"
        self.exact_url = "https://frinkiac.com/api/caption?"
        self.quote_url = "https://frinkiac.com/api/search?"
        self.meme_url = "https://frinkiac.com/meme/"
        self.season = None
        self.episode = None
        self.timestamp = None
        self.timestamp_end = None
        # self.duration = None
        self.quote = None
        self.valid_modes = ['random', 'quote', 'exact']
        self.mode = "random"
        self.regex_filter = re.compile("[^0-9A-Za-z ]")
        self.regex_episode = re.compile("^S\d+E\d+$")
        self.match_list = None
        self.search_result = None
        self.timestamp_list = None
        self.url_list = None
        self.meme_list = None
        self.ascii_meme_list = None
        self.data_list = None
        self.caption_list = None
        self.img_width = 120
        self.img_contrast = 1.0
        self.match_index = 0

    def _frinky_request(self, url):
        r = requests.get(url)
        if r.status_code == 200:
            json = r.json()
            return json
        else:
            return None

    def _filter_quote(self, quote):
        return self.regex_filter.sub("", str(quote))

    def string_to_season_episode(self, episode_string):
        s = episode_string.upper()
        if self.regex_episode.match(s):
            [season, episode] = s.split("E")
            season = int(season.replace("S", ""))
            episode = int(episode)
            return (season, episode)
        else:
            print(f"ERROR: {str(episode_string)} is not a valid episode format (SxxExx).")
            return None

    def season_episode_to_string(self, season, episode):
        return "S{:02}E{:02}".format(season, episode)

    def set_season(self, season):
        try:
            self.season = int(season)
        except ValueError:
            print(f"ERROR: {str(season)} is not an integer.")

    def set_episode(self, episode):
        try:
            self.episode = int(episode)
        except ValueError:
            print(f"ERROR: {str(episode)} is not an integer.")

    def set_timestamp(self, t_start, t_end=None):
        try:
            self.timestamp = int(t_start)
        except ValueError:
            print(f"ERROR: {str(t_start)} is not an integer.")
        if t_end is not None:
            try:
                self.timestamp_end = int(t_end)
            except ValueError:
                print(f"ERROR: {str(t_end)} is not an integer.")

    def set_timestamp_end(self, t_end):
        try:
            self.timestamp_end = int(t_end)
        except ValueError:
            print(f"ERROR: {str(t_end)} is not an integer.")

    def set_timestamp_end_from_duration(self, duration):
        try:
            ms = math.floor(float(duration) * 1000)
            self.timestamp_end = self.timestamp + ms
        except ValueError:
            print(f"ERROR: {str(duration)} is not a float.")

    def set_mode(self, mode):
        if mode in self.valid_modes:
            self.mode = mode
        else:
            print(f"ERROR: {str(mode)} not a valid mode.")
            print(f"Valid modes: {str(self.valid_modes)}.")

    def set_random(self):
        self.set_mode('random')

    def set_quote(self, quote):
        self.quote = self._filter_quote(quote)
        self.set_mode('quote')

    def set_exact(self, season, episode, timestamp, timestamp_end=None):
        self.set_season(season)
        self.set_episode(episode)
        self.set_timestamp(timestamp, timestamp_end)
        self.set_mode('exact')

    def search(self, mode=None, season=None, episode=None, timestamp=None, quote=None, set_result=True):
        if mode is None:
            mode = self.mode
        if season is None:
            season = self.season
        if episode is None:
            episode = self.episode
        if timestamp is None:
            timestamp = self.timestamp
        if quote is None:
            quote = self.quote
        if mode == 'random':
            url = self.random_url
        elif mode == 'exact':
            url = self.exact_url
            episode_string = self.season_episode_to_string(season, episode)
            query = urllib.parse.urlencode({"e": episode_string, "t": str(timestamp)})
            url = url + query
        elif mode == 'quote':
            url = self.quote_url
            query = urllib.parse.urlencode({"q": self._filter_quote(quote)})
            url = url + query
        else:
            print("ERROR: no valid search mode has been selected.")
        result = self._frinky_request(url)
        if set_result:
            if mode == 'quote':
                self.match_list = result
            else:
                self.search_result = result
            if mode == 'random':
                self.set_exact(result['Episode']['Season'], result['Episode']['EpisodeNumber'], result['Frame']['Timestamp'])
        return result

    def get_meme_url(self, season_episode, timestamp):
        episode_str = str(season_episode)
        timestamp_str = str(timestamp)
        return self.meme_url + episode_str + "/" + timestamp_str

    def get_meme_from_url(self, url):
        imgResponse = requests.get(url)
        return Image.open(BytesIO(imgResponse.content))

    def set_image_width(self, width):
        self.img_width = int(width)

    def set_image_contrast(self, contrast):
        self.img_contrast = float(contrast)

    def img2ascii(self, img):
        chars = np.asarray(list(' .~^:┐¡Γ░▒╠╬╣▓█'))
        wcf = 4/7  # width scaling factor to account for higher-than-wide characters
        # Set width
        S = (self.img_width, round(img.size[1] * wcf * self.img_width / img.size[0]))
        img = np.sum(np.asarray(img.resize(S)), axis=2)
        img -= img.min()
        img = (img / img.max()) ** self.img_contrast * (chars.size - 1)
        return "\n".join(("".join(r) for r in chars[img.astype(int)]))

    def preview_matches(self):
        idx = 0
        for match in self.match_list:
            episode = match["Episode"]
            timestamp = match["Timestamp"]
            url = self.get_meme_url(episode, timestamp)
            meme = self.get_meme_from_url(url)
            print(f"Episode: {episode}; Timestamp: {timestamp}; Index: {idx}")
            print(self.img2ascii(meme))
            print("=" * self.img_width)
            idx += 1

    def set_match_index(self, idx):
        try:
            if idx < 0:
                idx = 0
            elif idx >= len(self.match_list):
                idx = len(self.match_list) - 1
            self.match_index = idx
        except TypeError:
            print(f"ERROR: {str(idx)} is not a valid index for match list {str(self.match_list)}.")

    def set_match(self):
        match = self.match_list[self.match_index]
        (season, episode) = self.string_to_season_episode(match["Episode"])
        timestamp = match["Timestamp"]
        self.set_exact(season, episode, timestamp)
        pass

    def get_data_list(self, start_offset=0):
        ts = self.timestamp
        search_result = self.search_result
        data_list = [search_result]
        if self.timestamp_end is not None:
            while ts < self.timestamp_end:
                nearby = search_result['Nearby']
                times = [t for t in map(lambda x: x['Timestamp'], nearby)]
                ts_idx = times.index(ts)
                if ts_idx == len(times) - 1:
                    break
                else:
                    ts = times[ts_idx + 1]
                    search_result = self.search(mode='exact', season=self.season, episode=self.episode, timestamp=ts, set_result=False)
                    data_list.append(search_result)
        if float(start_offset) > 0:
            ts = self.timestamp
            search_result = self.search_result
            start_data_list = []
            new_start = ts - math.floor(float(start_offset) * 1000)
            while ts > new_start and new_start > 0:
                nearby = search_result['Nearby']
                times = [t for t in map(lambda x: x['Timestamp'], nearby)]
                ts_idx = times.index(ts)
                if ts_idx == 0:
                    break
                else:
                    ts = times[ts_idx - 1]
                    search_result = self.search(mode='exact', season=self.season, episode=self.episode, timestamp=ts, set_result=False)
                    start_data_list.append(search_result)
            start_data_list.reverse()
            data_list = start_data_list + data_list
        self.data_list = data_list

    def get_timestamp_list(self):
        self.timestamp_list = list(map(lambda x: x['Frame']['Timestamp'], self.data_list))
        # self.duration = (self.timestamp_list[-1] - self.timestamp_list[0]) / 1000

    def get_caption_list(self, sep="\n"):
        self.caption_list = [sep.join(map(lambda x: x['Content'], d['Subtitles'])) for d in self.data_list]

    def set_caption_list(self, caption):
        if isinstance(caption, str):
            self.caption_list = [caption]
        elif isinstance(caption, list) and False not in [isinstance(c, str) for c in caption]:
            self.caption_list = caption

    def get_url_list(self):
        episode = self.season_episode_to_string(self.season, self.episode)
        self.url_list = [self.get_meme_url(episode, t) for t in self.timestamp_list]

    def get_meme_list(self):
        self.meme_list = [self.get_meme_from_url(u) for u in self.url_list]

    def get_ascii_meme_list(self):
        self.ascii_meme_list = [self.img2ascii(m) for m in self.meme_list]

    def show_meme(self, index=0, index_end=None, animated=False, interval=0.2, loops=0, caption=True, print_info=False):
        if self.caption_list is None:
            caption = False
        if animated:
            ratio = None
            if index < 0:
                index = 0
            elif index >= len(self.ascii_meme_list):
                index = len(self.ascii_meme_list) - 1
            if index_end is not None and index_end <= index:
                index_end = index_end + 1
            if index_end is not None and index_end >= len(self.ascii_meme_list):
                index_end = None
            ascii_meme_list = self.ascii_meme_list[index:index_end]
            timestamp_list = self.timestamp_list[index:index_end]
            if caption:
                caption_list = self.caption_list[index:index_end]
                if len(self.caption_list) < len(self.ascii_meme_list):
                    ratio = len(self.caption_list) / len(self.ascii_meme_list)
            x = int(loops)
            while True:
                for i, meme in enumerate(ascii_meme_list):
                    os.system('clear')
                    print(meme)
                    if caption:
                        print("\n")
                        if ratio is None:
                            print(caption_list[i])
                        else:
                            print(caption_list[math.floor(i * ratio)])
                    if print_info:
                        print("\n")
                        print(f"({self.season_episode_to_string(self.season, self.episode)} @ {timestamp_list[i]})")
                    time.sleep(interval)
                if x == 1:
                    break
                elif x > 1:
                    x -= 1
        else:
            print(self.ascii_meme_list[index])
            if caption:
                if len(self.caption_list) != len(self.ascii_meme_list):
                    cap = self.caption_list[0]
                else:
                    cap = self.caption_list[index]
                print("\n")
                print(cap)
            if print_info:
                print("\n")
                print(f"({self.season_episode_to_string(self.season, self.episode)} @ {self.timestamp_list[index]})")


if __name__ == '__main__':
    args = check_args(sys.argv[1:])
    frinky = Frinky()
    frinky.set_image_width(args.width)
    frinky.set_image_contrast(args.contrast)
    if args.season != "" and args.episode != "" and args.timestamp != "":
        if args.endTimestamp != "":
            end = args.endTimestamp
        else:
            end = None
        frinky.set_exact(args.season, args.episode, args.timestamp, end)
        frinky.search()
    elif args.quote != "":
        frinky.set_quote(args.quote)
        frinky.search()
        if args.preview:
            frinky.preview_matches()
        else:
            frinky.set_match_index(args.match_index)
            frinky.set_match()
            frinky.search()
    elif args.random:
        frinky.set_random()
        frinky.search()
    else:
        frinky.set_random()
        frinky.search()
    if args.endTimestamp == "" and args.length != "":
        frinky.set_timestamp_end_from_duration(args.length)
    if frinky.search_result is not None:
        frinky.get_data_list()
        frinky.get_timestamp_list()
        frinky.get_url_list()
        frinky.get_meme_list()
        frinky.get_ascii_meme_list()
        frinky.get_caption_list()
        frinky.show_meme(animated=(args.gif and frinky.timestamp_end is not None), interval=args.interval, print_info=args.print_info)
#         furl, quote = get_random_meme_url_caption()
#     else:
#         furl = search_quote_get_meme_url(cmd_args.quote)
#         if cmd_args.caption == "":
#             quote = cmd_args.quote.upper()
#         else:
#             quote = cmd_args.caption.upper()
#     print(img2ascii(furl, width=cmd_args.width, GCF=cmd_args.gcf, url=True))
#     print("\n" + quote)
