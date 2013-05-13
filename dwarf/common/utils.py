#!/usr/bin/python


def show_request(req):
    print("---- BEGIN REQUEST HEADERS -----")
    for key in req.headers.keys():
        print('%s = %s' % (key, req.headers[key]))
    print("---- END REQUEST HEADERS -----")

#    if req.body:
#        print("---- BEGIN REQUEST BODY -----")
#        print('%s' % req.body)
#        print("---- END REQUEST BODY -----")
