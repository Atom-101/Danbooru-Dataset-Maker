import json
import glob
import os
from collections import defaultdict
import multiprocessing as mp
import sys
import tarfile

def get_files_worker(file,exclude_and,exclude_or,include_and,include_or,rating,classif,q):
    # files = sorted(glob.glob(f'{metadata_path}/*',recursive=True))
    # files = [f for f in files if os.path.isfile(f)]
    id_list,id_dict = [],defaultdict(lambda: [])
    if classif and not include_or: raise ValueError()
    try:
        with open(file) as f:
            print(f'Opened {file}')
            for line in f:
                js = json.loads(line)
                if rating and js['rating'] != rating: continue
                tag_dict = js['tags']
                tags = []
                for t in tag_dict:
                    tags.append(t['name'])
                tags = ' '.join(tags)
                if include_and is None or len([inc for inc in include_and if inc.lower() in tags]) == len(include_and):
                    if exclude_or is None or len([ex for ex in exclude_or if ex.lower() in tags]) == 0:
                        if exclude_and is None or len([ex for ex in exclude_or if ex.lower() in tags]) != len(exclude_and):
                            if include_or is None or len([inc for inc in include_or if inc.lower() in tags]) > 0:
                                if not classif:
                                    id_list.append(js['id'])
                                else:
                                    for tg in include_or:
                                        if tg in tags:  id_dict[tg].append(js['id'])
    except:
        pass    
    id_dict = dict(id_dict)
    print(f'Exiting {file}')
    q.put(id_list.copy() if not classif else id_dict.copy())
    return id_list if not classif else id_dict

def file_writer(q,classif):
    print('Writer called')
    if not classif:
        with open('tmp/id_list.txt','w') as f:
            print('Writing results to id_list')
            while(True):    
                msg = q.get()
                if msg == 'END':
                    break
                for id in msg:
                    print(f'*/{id}.*',file=f)
                    f.flush()
    else:
        while(True):
            msg = q.get()
            if msg=='END': break
            for k in msg.keys():
                with open(f'tmp/id_list_{k}.txt','w') as f:
                    print(f'Writing results to id_list_{k}')
                    for id in msg[k]:
                        print(f'*/{id}.*',file=f)
                        f.flush()
    print('Writer completed')

def handler(config_path):
    with open(config_path) as f:
        conf = json.load(f)
    os.makedirs('tmp',exist_ok=True)
    # print([k for k in conf.keys()])
    meta_path = conf['metadata_path']
    if meta_path is None:
        os.makedirs('tmp/meta',exist_ok=True)
        meta_path = 'tmp/meta'
        print('Getting metadata...')
        os.system('rsync -P --verbose --ignore-existing rsync://78.46.86.149:873/danbooru2019/metadata.json.tar.xz ./tmp/meta/')
        with tarfile.open('tmp/meta/metadata.json.tar.xz') as tar:
            tar.extractall('tmp/meta')
    classif = conf['classification']
    exclude_and,exclude_or,include_and,include_or = conf['exclude_and'],conf['exclude_or'],conf['include_and'],conf['include_or']
    rating = conf['rating']
    manager = mp.Manager()
    q = manager.Queue()    
    pool = mp.Pool(mp.cpu_count() + 2)
    pool.apply_async(file_writer,(q,classif))

    json_files = sorted(glob.glob(f'{meta_path}/*',recursive=True))
    json_files = [f for f in json_files if os.path.isfile(f)]
    if len(json_files) == 0:
        raise AttributeError('No metadata files found. Please recheck path')
    json_files = json_files
    jobs = []
    for file in json_files:
        job = pool.apply_async(get_files_worker,(file,exclude_and,exclude_or,include_and,include_or,rating,classif,q))
        jobs.append(job)
    
    for job in jobs:
        job.get()
    
    q.put("END")
    pool.close()
    pool.join()

if __name__ == "__main__":
    handler(sys.argv[1])
                    
                    
