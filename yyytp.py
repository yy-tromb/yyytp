import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

from send2trash import send2trash as trash
from yt_dlp import YoutubeDL

args = sys.argv


def join_diacritic(text, mode="NFC"):
    bytes_text = text.encode()

    bytes_text = re.sub(b"\xe3\x82\x9b", b"\xe3\x82\x99", bytes_text)
    bytes_text = re.sub(b"\xef\xbe\x9e", b"\xe3\x82\x99", bytes_text)

    bytes_text = re.sub(b"\xe3\x82\x9c", b"\xe3\x82\x9a", bytes_text)
    bytes_text = re.sub(b"\xef\xbe\x9f", b"\xe3\x82\x9a", bytes_text)

    text = bytes_text.decode()
    text = unicodedata.normalize(mode, text)

    return text


if len(args) <= 1 or (type(args[1]) is not str) or not (args[1].startswith("https://")):
    print("""Usage yyyt.py \"URL\" (-no-cache) (-debug)""")
    exit(1)
else:
    with YoutubeDL({}) as ydl:
        URL = args[1].split("&list=")[0]
        if URL.startswith("https://youtu.be/"):
            ID = URL.split("/")[-1]
        else:
            ID = URL.split("?v=")[1]

        if (
            os.path.isfile("./.__yyytp_cache")
            and len(args) >= 3
            and args[2] != "-no-cache"
        ):
            cache = open("./.__yyytp_cache", mode="r")
            cache_json = json.load(cache)
            if cache_json["id"] == ID:
                info = cache_json
                use_cache = True
            else:
                extract_info = ydl.extract_info(URL, download=False)
                info = ydl.sanitize_info(extract_info)
                __yyytp_cache = open("./.__yyytp_cache", mode="w")
                __yyytp_cache.write(json.dumps(info))
                use_cache = False

        else:
            extract_info = ydl.extract_info(URL, download=False)
            info = ydl.sanitize_info(extract_info)
            __yyytp_cache = open("./.__yyytp_cache", mode="w")
            __yyytp_cache.write(json.dumps(info))
            use_cache = False

        __fulltitle = info["fulltitle"].replace("/", "／").replace("\\", "¥")
        fulltitle = join_diacritic(__fulltitle)

    format_info = {"AV1": None, "VP9": None, "H264": None, "Opus": None, "AAC": None}
    ql_info = {"AV1": None, "VP9": None, "H264": None}
    for format in info["formats"]:
        if format["vcodec"].startswith("av01"):
            format_info["AV1"] = format["format_id"]
            ql_info["AV1"] = format["format_note"]

        elif format["vcodec"] == "vp9":
            format_info["VP9"] = format["format_id"]
            ql_info["VP9"] = format["format_note"]

        elif format["vcodec"].startswith("avc1") and format["acodec"] == "none":
            format_info["H264"] = format["format_id"]
            ql_info["H264"] = format["format_note"]

        elif format["acodec"] == "opus":
            format_info["Opus"] = format["format_id"]

        elif format["acodec"].startswith("mp4a") and format["vcodec"] == "none":
            format_info["AAC"] = format["format_id"]

    dl_format = ""
    dl_codec = {"AV1": False, "VP9": False, "H264": False, "Opus": False, "AAC": False}

    for key, itag in format_info.items():
        if itag is None:
            print(key + " is not found")
        elif key != "AV1" and key != "Opus":
            dl_format += itag + ","
            dl_codec[key] = True
        else:
            dl_codec[key] = True

    dl_format = dl_format[:-1]

    exist_file = ""
    # check exist file
    if os.path.isfile(fulltitle + ".webm"):
        exist_file += fulltitle + ".webm "

    if os.path.isfile(fulltitle + ".mp4"):
        exist_file += fulltitle + ".mp4 "

    if os.path.isfile(fulltitle + ".m4a"):
        exist_file += fulltitle + ".m4a "

    if os.path.isfile(fulltitle + ".mka"):
        exist_file += fulltitle + ".mka "

    if os.path.isfile(fulltitle + "_av1.mp4"):
        exist_file += fulltitle + "_av1.mp4 "

    if os.path.isfile(fulltitle + ".mkv"):
        exist_file += fulltitle + ".mkv "
    # End

    if exist_file != "":
        print("%s file(s) exist" % exist_file)
        exit(1)

    print(
        f"""

   download
AV1: {format_info['AV1']} {ql_info['AV1']}
VP9: {format_info['VP9']} {ql_info['VP9']}
H264 {format_info['H264']} {ql_info['H264']}

Opus {format_info['Opus']}
AAC {format_info['AAC']}

   """
    )

    dl_opt = {"format": dl_format, "outtmpl": f"{fulltitle}.%(ext)s"}
    with YoutubeDL(dl_opt) as ydl:
        if use_cache is True:
            ydl.download_with_info_file("./.__yyytp_cache")
        else:
            ydl.download(URL)

    if format_info["Opus"] is not None:
        dl_opus_opt = {"format": format_info["Opus"], "outtmpl": f"{fulltitle}.mka"}
        with YoutubeDL(dl_opus_opt) as ydl_opus:
            if use_cache is True:
                ydl_opus.download_with_info_file("./.__yyytp_cache")
            else:
                ydl_opus.download(URL)

    if format_info["AV1"] is not None:
        dl_av1_opt = {"format": format_info["AV1"], "outtmpl": f"{fulltitle}_av1.mp4"}
        with YoutubeDL(dl_av1_opt) as ydl_av1:
            if use_cache is True:
                ydl_av1.download_with_info_file("./.__yyytp_cache")
            else:
                ydl_av1.download(URL)


try:
    target_video = ""
    target_audio = ""
    # select video
    if dl_codec["AV1"] is True:
        target_video = fulltitle + "_av1.mp4"
    elif dl_codec["VP9"] is True:
        target_video = fulltitle + ".webm"
    elif dl_codec["H264"] is True:
        target_video = fulltitle + ".mp4"
    else:
        print("No Videos")
        exit(1)

    # select audio
    if dl_codec["Opus"] is True:
        target_audio = fulltitle + ".mka"
    elif dl_codec["AAC"] is True:
        target_audio = fulltitle + ".m4a"
    else:
        print("No Audios")
        exit(1)

    cmd = [
        "ffmpeg",
        "-i",
        target_video,
        "-i",
        target_audio,
        "-c",
        "copy",
        fulltitle + ".mkv",
    ]
    res = subprocess.run(
        cmd, capture_output=True, check=True, text=True, encoding="utf-8"
    )
except subprocess.CalledProcessError as error:
    print(error.cmd)
    print("code: " + str(error.returncode))
    print("output: " + error.output)
    print("stdout: " + error.stdout)
    print("stderr: " + error.stderr)
    exit(1)

print("returncode=", str(res.returncode))

# for debug
if len(args) >= 3 and (
    args[2] == "-debug" or (args[2] == "-no-cache" and args[3] == "-debug")
):
    print(fulltitle)
    print(f"format_info: {format_info}")
    print(f"ql_info: {ql_info}")
    print(f"dl_format: {dl_format}")
    print(f"dl_codec: {dl_codec}")
    print(f"dl_opt: {dl_opt}")
    print(f"dl_opus_opt: {dl_opus_opt}")
    if dl_codec["AV1"] is True:
        print(f"dl_av1_opt: {dl_av1_opt}")
    print(f"exist_file: {exist_file}")
    print(f"target_video: {target_video}")
    print(f"target_audio: {target_audio}")
    print(f"stdout: {res.stdout}")
    print(f"stderr: {res.stderr}")

if not os.path.isdir("./src"):
    print(
        "./src is not found. so can't move files. Do you want to make src dir? \n\
        y or n"
    )
    make_src_dir = input()
    if make_src_dir == "y" or make_src_dir == "Y":
        os.mkdir("./src")
    else:
        print("exit...")
        exit(0)


try:
    shutil.move(fulltitle + ".mp4", "./src")
    if dl_codec["AV1"] is True:
        trash(fulltitle + "_av1.mp4")
        shutil.move(fulltitle + ".webm", "./src")
    elif dl_codec["VP9"] is True:
        trash(fulltitle + ".webm")

    if os.path.isdir("./movie"):
        shutil.move(fulltitle + ".mkv", "./movie")
    elif os.path.isdir("./video"):
        shutil.move(fulltitle + ".mkv", "./video")
except all as ferror:
    print("Error @ move file")
    print(ferror)
    exit(1)
print("exit...")
exit(0)
