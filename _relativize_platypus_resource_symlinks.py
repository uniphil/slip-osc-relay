import os

resource_base = 'SLIP-UDP Relay.app/Contents/Resources'
resource_depth = len(resource_base.split('/'))
resource_rel = ''.join(('../',) * resource_depth)
for fname in os.listdir(resource_base):
    fpath = os.path.join(resource_base, fname)
    if not os.path.islink(fpath):
        print 'skipping non-link', fpath
        continue
    ftarget = os.readlink(fpath)
    if not os.path.isabs(ftarget):
        print 'link already relative:', ftarget
        continue
    prefix = os.path.commonprefix((os.getcwd(), ftarget))
    deprefixed = ftarget[len(prefix) + 1:]
    relative_dest = os.path.join(resource_rel, deprefixed)
    print 'removing link at', fpath
    os.remove(fpath)
    print 'recreating link as relative: ', fpath, '->', relative_dest
    os.symlink(relative_dest, fpath)
