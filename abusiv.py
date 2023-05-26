import aiofiles
import aiohttp
import datetime
import yarl

from bs4 import BeautifulSoup
from pathlib import Path

def get_ItemFromTag_h5ai(tag,the_odir,reslist):

	tag_td_icon=tag.find("td",attrs={"class":"fb-i"})
	tag_td_link=tag.find("td",attrs={"class":"fb-n"})
	if (not tag_td_icon) or (not tag_td_link):
		return

	tag_img=tag_td_icon.find("img")
	if not tag_img:
		return

	fse_type_raw=tag_img.get("alt")
	if (not fse_type_raw) or (not fse_type_raw in ["file","folder"]):
		return

	fse_type={"file":"f","folder":"d"}[fse_type_raw]

	tag_a=tag_td_link.find("a")
	if not tag_a:
		return

	the_url=tag_a.get("href")
	the_name=tag_a.text.strip()

	reslist.append({"type":fse_type,"url":the_url,"odir":the_odir,"name":the_name})

def get_TagsFromBTag(tags_all,outdir,atype):

	# Get relevant tags from master tag

	if atype=="h5ai":
		tag_body=tags_all.find("body",id="root")
		if not tag_body:
			return []

		tag_div1=tag_body.find("div",id="fallback")
		if not tag_div1:
			return []

		tag_table=tag_div1.find("table")
		tags_tr=tag_table.find_all("tr")
		if len(tags_tr)<3:
			return []

		tags_target=tags_tr[2:]

	# Get items from relevant tags

	results=[]

	if atype=="h5ai":
		for tag in iter(tags_target):
			get_ItemFromTag_h5ai(tag,outdir,results)

	return results

async def download_page(session,url):
	print(f"\n- Obtaining tags from: {url}")
	try:
		async with session.get(url) as response:
			#if not response.headers.get("Content-Type")=="text/html":
			#	raise Exception("Expected text/html content")
			html_dump=await response.text()
	except Exception as e:
		print(f"  Error: {e}")
		return None

	print("  OK")
	return BeautifulSoup(html_dump,"lxml")

async def download_file(session,url,filepath):
	print(f"\n- Downloading file\n  URL: {url}\n  Filepath: {filepath}")
	if filepath.exists():
		print("  The file already exists")
		return

	mb=1024*1024
	filepath.parent.mkdir(parents=True,exist_ok=True)
	try:
		async with session.get(url) as response:
			async with aiofiles.open(f"{filepath}","wb") as file:
				while True:
					chunk=await response.content.read(mb)
					if not chunk:
						break
					await file.write(chunk)
	except Exception as e:
		msg=f"Error: {e}"
	else:
		msg="Ok"

	print(f"  {msg}")

async def processor(session,itemlist,yurl,atype):
	item=itemlist.pop()

	print(f"\n- Processing the following item:\n  {item}")

	item_type=item.get("type")
	item_url=item.get("url")
	item_name=item.get("name")
	item_odir=item.get("odir")

	if atype=="h5ai":
		item_url=yurl.scheme+"://"+yurl.host+item_url

	outpath=item_odir.joinpath(item_name)

	if item_type=="f":
		await download_file(session,item_url,outpath)
		return

	tags_all=await download_page(session,item_url)
	if not tags_all:
		return

	items_recovered=get_TagsFromBTag(tags_all,outpath,atype)
	for item in items_recovered:
		itemlist.append(item)

async def manager(basedir_raw,atype,url_main):
	yurl=yarl.URL(url_main)
	session=aiohttp.ClientSession()
	tags_all=await download_page(session,url_main)
	if not tags_all:
		return

	basedir=Path(basedir_raw)
	if basedir.exists():
		basedir=Path(f"{basedir_raw}.{datetime.now()}")
		basedir.mkdir(parents=True,exist_ok=True)

	items=get_TagsFromBTag(tags_all,basedir,atype)
	while True:
		if len(items)==0:
			break

		await processor(session,items,yurl,atype)

	await session.close()

if __name__=="__main__":

	import sys
	import asyncio

	app_name=Path(sys.argv[0]).name

	if not len(sys.argv)==4:
		print(f"\nUSAGE:\n\n$ {app_name} BASEDIR ATYPE URL\n\nAvailable Autoindex Types:\n- h5ai\n\nv2023-05-26 by Carlos Alberto González Hernández")
		exit(1)

	bd=sys.argv[1]
	atype=sys.argv[2]
	url=sys.argv[3]

	asyncio.run(manager(bd,atype,url))
