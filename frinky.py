#!/Users/michaelgeaghan/anaconda3/envs/frinky/bin/python 
import requests
from PIL import Image
import numpy as np
from io import BytesIO
import math

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

def f2a(width = 100, GCF = 0.035):
	furl, quote = get_quote()
	img2ascii(furl, width = width, GCF = GCF, url = True)
	print("\n" + quote)

if __name__ == '__main__':
    f2a(width = 120, GCF = 1)

