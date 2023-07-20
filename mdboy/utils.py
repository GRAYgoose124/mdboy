def flatten(container):
    """ From https://stackoverflow.com/a/10824420 """
    for i in container:
        if isinstance(i, (list,tuple)):
            for j in flatten(i):
                yield j
        else:
            yield i