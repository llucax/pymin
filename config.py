# vim: set et sts=4 sw=4 encoding=utf-8 :

# XXX for testing only
def test_func(*args):
    print 'func:', args

routes = dict \
(
    test = test_func,
)

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)

