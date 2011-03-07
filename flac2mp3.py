#!/usr/bin/python

import os
import os.path
import sys
import re
import shutil
from stat import *

IN_DIR   = "C:\\media\\audio\\FLAC"
OUT_DIR  = "C:\\media\\audio\\MP3"
LAME     = "C:\\Documents and Settings\\staffan\\bin\\i386-pc-win32\\lame.exe"
FLAC     = "C:\\Documents and Settings\\staffan\\bin\\i386-pc-win32\\flac.exe"
METAFLAC = "C:\\Documents and Settings\\staffan\\bin\\i386-pc-win32\\metaflac.exe"

# This path must not contain spaces (it can't be quoted in the
# os.system call for some reason), hence the short name (~1) form
FLAC     = "C:\\PROGRA~1\\FLAC\\flac.exe" 
METAFLAC = "C:\\PROGRA~1\\FLAC\\metaflac.exe"

genres = {}

def init_genres():
    cmd = '"%s" --genre-list' % LAME
    print "init_genres: cmd %s" %cmd
    pipe = os.popen(cmd, "r")
    for g in pipe.read().splitlines():
        m = re.match(r'^ *(\d+)\ +(.*)', g)
        if m:
            # print "init_genres: %s has id %s" % (m.group(2),m.group(1))
            genres[m.group(2)] = m.group(1)

def do_dir(dirname):
    indir = os.path.abspath(dirname)
    outdir = indir.replace(IN_DIR,OUT_DIR)
    assert(indir!=outdir)
    # print "converting from '%s' to '%s'" % (indir,outdir)
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    m3ufile = open("%s/playlist.m3u"%outdir, "w")
    for f in os.listdir(indir):
        if f.endswith(".flac"):
            flac_to_mp3(indir,f,outdir,m3ufile)
        elif f != "playlist.m3u":
            print "copying %s" % f
            try:
                shutil.copy2("%s/%s" % (indir,f), "%s/%s" % (outdir,f))
            except IOError:
                print "Oops, IOError occurred, oh well"
                
    m3ufile.close()

def flac_to_mp3(indir,filename,outdir,m3ufile):
    fields = {}
    cmd = '%s --no-utf8-convert --export-tags-to - "%s%s%s"' % (METAFLAC,
                                                                indir,
                                                                os.sep,
                                                                filename)

    fields_str = unicode(os.popen(cmd, "r").read(),'utf-8').encode('iso-8859-1')

    for line in fields_str.splitlines():
        print "line: '%s'" % line
        (key,val) = line.split("=",1)
        fields[key.lower()] = val
    
    fields['tracknumber'] = "%2.2d" % int(fields['tracknumber'])

    if not fields['genre'] in genres:
        print "Genre '%s' not recognized" % fields['genre']
        fields['genre'] = "Rock"

    outfile = "%s-%s-%s.mp3" % (fields['tracknumber'],
                                fields['artist'],
                                fields['title'])
    outfile = re.sub('[\\:/\*\?<>|]','',outfile) # remove characters illegal in NTFS
    m3ufile.write("%s\n" % outfile)
    if os.path.exists("%s%s%s" % (outdir, os.sep, outfile)):
        print "Outfile %s%s%s exists, skipping" % (outdir, os.sep, outfile)
        return
    print "outfile is %s" % outfile

    if (fields['artist']      != "" and
        fields['title']       != "" and
        fields['tracknumber'] != "" and
        fields['album']       != ""):
        

	# if you care about quality as opposed to filesize, use
	# --preset standard or something instead of -V 6
        cmd = '%s -s -c -d "%s%s%s" | "%s" -V 6 --ty %s --ta "%s" --tl "%s" --tt "%s" --tg "%s" --tn %s --add-id3v2 --quiet - "%s%s%s"' % (
            FLAC,
            indir, os.sep, filename,
            LAME,
            fields['date'],
            fields['artist'],
            fields['album'],
            fields['title'],
            fields['genre'],
            fields['tracknumber'],
            outdir, os.sep, outfile)
        print "executing %s" % cmd
        os.system(cmd)
    else:
	print "%s: couldn't find enough comments in flac file (need artist+title+album+tracknum, skipping this file!" % filename


if __name__ == "__main__":
    init_genres()

    if len(sys.argv) < 2:
        dirs = os.listdir(os.getcwd())
    else:
        dirs = sys.argv[1:]

    for dir in dirs:
        if not S_ISDIR(os.stat(dir)[ST_MODE]):
            print "'%s' is not a directory" % dir
            continue
        do_dir(dir)
