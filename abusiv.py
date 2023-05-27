import aiofiles
import aiohttp
import datetime
import yarl

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import unquote as url_to_text

def get_ItemFromTag_apache2(tag,the_odir,reslist,path_origin):
	tag_td_icon=tag.find("td",attrs={"valign":"top"})
	tag_a=tag.find("a")
	if (not tag_td_icon) or (not tag_a):
		return

	tag_img=tag_td_icon.find("img")
	if not tag_img:
		return

	the_type_raw=tag_img.get("alt")
	if (not the_type_raw):
		return

	if the_type_raw=="[DIR]":
		fse_type="d"

	if not the_type_raw=="[DIR]":
		if the_type_raw=="[PARENTDIR]":
			return

		fse_type="f"

	the_url_raw=tag_a.get("href")
	the_url=url_to_text(the_url_raw)
	if not the_url.startswith("/"):
		the_url=str(path_origin.joinpath(the_url))

	the_name=tag_a.text.strip()

	reslist.append({"type":fse_type,"url":the_url,"odir":the_odir,"name":the_name})

def get_ItemFromTag_h5ai(tag,the_odir,reslist):

	tag_td_icon=tag.find("td",attrs={"class":"fb-i"})
	tag_td_link=tag.find("td",attrs={"class":"fb-n"})
	if (not tag_td_icon) or (not tag_td_link):
		return

	tag_img=tag_td_icon.find("img")
	if not tag_img:
		return

	the_type_raw=tag_img.get("alt")
	if (not the_type_raw) or (not the_type_raw in ["file","folder"]):
		return

	fse_type={"file":"f","folder":"d"}[the_type_raw]

	tag_a=tag_td_link.find("a")
	if not tag_a:
		return

	the_url=tag_a.get("href")
	the_url=url_to_text(the_url)
	the_name=tag_a.text.strip()

	reslist.append({"type":fse_type,"url":the_url,"odir":the_odir,"name":the_name})

def get_TagsFromBTag(tags_all,url_curr,outdir,atype):

	# Get relevant tags from master tag

	if atype=="apache2":
		tag_table=tags_all.find("table")
		if not tag_table:
			return []

		tags_tr=tag_table.find_all("tr")
		if len(tags_tr)<3:
			return []

		tags_target=tags_tr[2:]

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

	if atype=="apache2":
		path_origin=Path(yarl.URL(url_curr).path)

	for tag in iter(tags_target):
		if atype=="apache2":
			get_ItemFromTag_apache2(tag,outdir,results,path_origin)

		if atype=="h5ai":
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

	if atype=="h5ai" or atype=="apache2":
		item_url=yurl.scheme+"://"+yurl.host+item_url

	outpath=item_odir.joinpath(item_name)

	if item_type=="f":
		await download_file(session,item_url,outpath)
		return

	tags_all=await download_page(session,item_url)
	if not tags_all:
		return

	items_recovered=get_TagsFromBTag(tags_all,item_url,outpath,atype)
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
		if basedir.is_file():
			print(f"\nERROR: The output path matches an existing file. Aborting now")
			return

	basedir.mkdir(parents=True,exist_ok=True)

	items=get_TagsFromBTag(tags_all,url_main,basedir,atype)
	while True:
		if len(items)==0:
			break

		await processor(session,items,yurl,atype)

	await session.close()

if __name__=="__main__":

	import sys
	import asyncio

	app_name=Path(sys.argv[0]).name

	atypes=["apache2","h5ai"]

	if not len(sys.argv)==4:
		print(f"\nUSAGE:\n\n$ {app_name} BASEDIR ATYPE URL")
		print("\nAvailable Autoindex Types:\n")
		for t in atypes:
			print(f"- {t}")

		print("\nWritten by Carlos Alberto González Hernández\nVersion: 2023-05-27\n")
		sys.exit(1)

	bdir=sys.argv[1]
	atype=sys.argv[2]
	url=sys.argv[3]

	atype=atype.strip()
	atype=atype.lower()

	if not atype in atypes:
		print(f"\nERROR: Unknown autoindex type '{atype}'\n\nAvailable Autoindex Types:\n")
		for t in atypes:
			print(f"- {t}")

		sys.exit(1)

	app_dir=Path(sys.argv[0]).parent
	if app_dir.resolve()==Path(bdir).resolve():
		print("\nERROR: Use a different directory")
		sys.exit(1)

	asyncio.run(manager(bdir,atype,url))
	print("\nProgram finished!")
	sys.exit(0)
