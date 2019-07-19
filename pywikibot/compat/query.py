# -*- coding: utf-8 -*-
"""
WARNING: THIS MODULE EXISTS SOLELY TO PROVIDE BACKWARDS-COMPATIBILITY.

Do not use in new scripts; use the source to find the appropriate
function/method instead.

"""
#
# (C) Pywikibot team, 2008-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot.data import api
from pywikibot.tools import deprecated, deprecate_arg

import io


@deprecated('pywikibot.data.api.Request', since='20120603')
@deprecate_arg('useAPI', None)
@deprecate_arg('retryCount', None)
@deprecate_arg('encodeTitle', None)
def GetData(request, site=None, back_response=False):
    """
    Query the server with the given request dict.

    DEPRECATED: Use pywikibot.data.api.Request instead.
    """
    if site:
        request['site'] = site

    req = api.Request(**request)
    result = req.submit()

    if back_response:
        pywikibot.warning('back_response is no longer supported; an empty '
                          'response object will be returned')
        res_dummy = io.StringIO()
        res_dummy.__dict__.update({'code': 0, 'msg': ''})
        return res_dummy, result
    return result
