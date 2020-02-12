with open('traceout') as f:
    fn = open('new_traceout','w')
    for l in f.readlines():
        if "EINVAL" in l or "ENOENT" in l:
            continue
        else:
            fn.writelines(l)

fn.close()
