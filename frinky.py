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
	parser.add_argument('-s', '--season', help="Specify a season. Must be used in conjunction with -e/--episode.", default="")
	parser.add_argument('-e', '--episode', help="Specify an episode. Must be used in conjunction with -s/--season.", default="")
	parser.add_argument('-t', '--timestamp', help="Specify a timestamp. Must be used in conjunction with -s/--season and -e/--episode.", default="")
	parser.add_argument('-T', '--endTimestamp', help="Specify an endpoint timestamp. Must be used in conjunction with -s/--season, -e/--episode, and -t/--timestamp. Only used when using -G/--gif.")
	parser.add_argument('-G', '--gif', help="Specify an animation should be returned with specified length starting from first best match or from specified timestamp of specified episode. Must either specify a duration with -l/--length or an endpoint timestamp with -T/--endTimestamp.", action="store_true")
	parser.add_argument('-l', '--length', help="Specify length (in seconds) of animation to be returned. Only used in conjunction with -G/--gif.")
	parser.add_argument('-C', '--char', help="Specify a character set (e.g. 0, 1, 2, ...). Use if the default set doesn't work well. Default = '0'.", default="0")
	parser.add_argument('-w', '--width', help="ASCII art width.", default="120")
	parser.add_argument('-g', '--gcf', help="Scaling factor.", default="1")
	arguments = parser.parse_args(args)
	arguments.width = int(arguments.width)
	arguments.gcf = float(arguments.gcf)
	return(arguments)

def get_quote():
	r = requests.get("https://frinkiac.com/api/random")
	if r.status_code == 200:
		json = r.json()
		# Extract the episode number and timestamp from the API response
		# and convert them both to strings.
		id, episode, timestamp = map(str, json["Frame"].values())
		image_url = "https://frinkiac.com/meme/" + episode + "/" + timestamp
		# Combine each line of subtitles into one string.
		caption = "\n".join([subtitle["Content"] for subtitle in json["Subtitles"]])
		return image_url, caption

def search_quote(quote_str, episode=None):
	url = "https://frinkiac.com/api/search?"
	quote = urllib.parse.urlencode({"q": quote_str})
	url = url + quote
	r = requests.get(url)
	if r.status_code == 200:
		json = r.json()
		tophit = json[0]
		ep = tophit["Episode"]
		ts = tophit["Timestamp"]
		image_url = "https://frinkiac.com/meme/" + ep + "/" + str(ts)
		return image_url

def img2ascii(f, width = 100, GCF = 0.035, url = False):
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
	img = np.sum( np.asarray( img.resize(S) ), axis=2)
	img -= img.min()
	img = (img/img.max())**GCF*(chars.size-1)
	# img = 1/(1 + math.e**(-GCF*(((img - img.min())- ((img.max() - img.min())/2)) - 0.5)))*(chars.size-1)
	# img = (1*((img - img.min()))/(2*(img.max() - img.min())))**GCF*(chars.size-1)
	print( "\n".join( ("".join(r) for r in chars[img.astype(int)]) ) )

if __name__ == '__main__':
	cmd_args = check_args(sys.argv[1:])
	if cmd_args.random:
		furl, quote = get_quote()
	else:
		furl = search_quote(cmd_args.quote)
		if cmd_args.caption == "":
			quote = cmd_args.quote.upper()
		else:
			quote = cmd_args.caption.upper()
	img2ascii(furl, width=cmd_args.width, GCF=cmd_args.gcf, url=True)
	print("\n" + quote)
	
