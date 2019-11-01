def split_skip_empty_parts(str, sep=' '):
    return list(filter(None, str.split(sep)))
