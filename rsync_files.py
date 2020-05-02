import sys
import os
import glob
import argparse
from generate_file_list import handler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download Danbooru2019 images')
    parser.add_argument("-o","--original",help="Download from original dataset. Default behavior is to use the 512px dataset", action="store_true")
    parser.add_argument("-s","--skip-file-list",help="Don't create the file list before calling rsync. Will assume that file list(s) exist in tmp directory in current path", action="store_true")
    parser.add_argument("-c","--config-path",help="Path to config.json file. Defaults to current directory",default="")
    args = parser.parse_args()
    ftype = "original" if args.original else "512px"
    if not args.skip_file_list:
        print("Making file list(s)...")
        handler(args.config_path+"config.json")

    files = glob.glob('tmp/*.txt')
    if len(files) > 1:
        for file in files:
            path = file[:-4].split('_')[-1]
            os.makedirs(path, exist_ok=True)
            os.system(f'rsync -P --recursive --verbose  --include="*/" --include-from={file} --exclude="*" --ignore-existing --relative rsync://78.46.86.149:873/danbooru2019/{ftype}/ ./{path}/') 
            os.system(f'find {path}/{ftype}/ -mindepth 2 -type f -print -exec mv {{}} {path} \\;')
            os.system(f'find {path}/{ftype}/ -empty -type d -delete')
    else:
        path = "dataset"
        file = files[0]
        os.makedirs(path, exist_ok=True)
        os.system(f'rsync -P --recursive --verbose  --include="*/" --include-from={file} --exclude="*" --ignore-existing --relative rsync://78.46.86.149:873/danbooru2019/{ftype}/ ./{path}/') 
        os.system(f'find {path}/{ftype}/ -mindepth 2 -type f -print -exec mv {{}} {path} \\;')
        os.system(f'find {path}/{ftype}/ -empty -type d -delete')


