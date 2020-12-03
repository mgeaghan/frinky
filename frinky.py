#!/usr/bin/env python3
import requests
from PIL import Image
import numpy as np
from io import BytesIO
import math
import urllib
import argparse
import sys


def check_args(args=None):
    parser = argparse.ArgumentParser(description="Get an ASCII image from frinkiac. Either search for a quote or get a randome one!", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-r', '--random', help="Get a random quote.", action="store_true")
    parser.add_argument('-q', '--quote', help="Search for a quote.", default="may god have mercy on us all")
    parser.add_argument('-c', '--caption', help="Custom caption.", default="")
    parser.add_argument('-s', '--season', help="Specify a season. Must be used in conjunction with -e/--episode and -t/--timestamp.", default="")
    parser.add_argument('-e', '--episode', help="Specify an episode. Must be used in conjunction with -s/--season and -t/--timestamp.", default="")
    parser.add_argument('-t', '--timestamp', help="Specify a timestamp. Must be used in conjunction with -s/--season and -e/--episode.", default="")
    parser.add_argument('-T', '--endTimestamp', help="Specify an endpoint timestamp. Must be used in conjunction with -s/--season, -e/--episode, and -t/--timestamp. Only used when using -G/--gif.")
    parser.add_argument('-G', '--gif', help="Specify an animation should be returned with specified length starting from first best match or from specified timestamp of specified episode. Must either specify a duration with -l/--length or an endpoint timestamp with -T/--endTimestamp.", action="store_true")
    parser.add_argument('-l', '--length', help="Specify length (in seconds) of animation to be returned. Only used in conjunction with -G/--gif.")
    parser.add_argument('-S', '--speed', help="Specify the speed at which an animation plays. 1 = normal rate. Only used in conjunction with -G/--gif. Default = '1'.", default="1")
    parser.add_argument('-C', '--char', help="Specify a character set (e.g. 0, 1, 2, ...). Use if the default set doesn't work well. Default = '0'.", default="0")
    parser.add_argument('-w', '--width', help="ASCII art width.", default="120")
    parser.add_argument('-g', '--gcf', help="Scaling factor.", default="1")
    parser.add_argument('-R', '--report', help="Print a human-readable report of the results of a search.", action="store_true")
    arguments = parser.parse_args(args)
    arguments.width = int(arguments.width)
    arguments.gcf = float(arguments.gcf)
    return(arguments)


def frinky_request(url):
    r = requests.get(url)
    if r.status_code == 200:
        json = r.json()
        return json
    else:
        return None


def get_random_json():
    return frinky_request("https://frinkiac.com/api/random")


def get_random_frame_caption():
    json = get_random_json()
    if json is None:
        return None
    frame_id, episode, timestamp = map(str, json["Frame"].values())
    image_url = "https://frinkiac.com/meme/" + episode + "/" + timestamp
    # Combine each line of subtitles into one string.
    caption = "\n".join([subtitle["Content"] for subtitle in json["Subtitles"]])
    return image_url, caption


def search_quote_get_json(quote_str):
    url = "https://frinkiac.com/api/search?"
    quote = urllib.parse.urlencode({"q": quote_str})
    url = url + quote
    return frinky_request(url)


def search_quote_get_frame(quote_str):
    json = search_quote_get_json(quote_str)
    if json is None:
        return None
    tophit = json[0]
    ep = tophit["Episode"]
    ts = tophit["Timestamp"]
    image_url = "https://frinkiac.com/meme/" + ep + "/" + str(ts)
    return image_url


def img2ascii(f, width=120, GCF=1.0, url=True):
    chars = np.asarray(list(' .~^:┐¡Γ░▒╠╬╣▓█'))
    # WCF = width scaling factor to account for higher-than-wide characters
    WCF = 4/7
    if url:
        imgResponse = requests.get(f)
        img = Image.open(BytesIO(imgResponse.content))
    else:
        img = Image.open(f)
    # Set width
    S = (width, round(img.size[1]*WCF*width/img.size[0]))
    img = np.sum(np.asarray(img.resize(S)), axis=2)
    img -= img.min()
    img = (img / img.max()) ** GCF * (chars.size - 1)
    # img = 1/(1 + math.e**(-GCF*(((img - img.min())- ((img.max() - img.min())/2)) - 0.5)))*(chars.size-1)
    # img = (1*((img - img.min()))/(2*(img.max() - img.min())))**GCF*(chars.size-1)
    print("\n".join(("".join(r) for r in chars[img.astype(int)])))


if __name__ == '__main__':
    cmd_args = check_args(sys.argv[1:])
    if cmd_args.random:
        furl, quote = get_random_frame_caption()
    else:
        furl = search_quote_get_frame(cmd_args.quote)
        if cmd_args.caption == "":
            quote = cmd_args.quote.upper()
        else:
            quote = cmd_args.caption.upper()
    img2ascii(furl, width=cmd_args.width, GCF=cmd_args.gcf, url=True)
    print("\n" + quote)
