# coding: utf-8

from django.shortcuts import render_to_response, get_object_or_404
import os
from string import replace
from django.conf import settings as s
from django.http import Http404, HttpResponse
from django.utils import simplejson 
from shutil import copyfile

"""
TODO:
check save before open new file
auto backup before save OR backup UI key
log changes

"""

filetypes = {
    '.py':      ( u'Python', '"parsepython.js"', '"/media/dj/codemirror/css/pythoncolors.css"'  ),
    '.html':    ( u'HTML', '["tokenizejavascript.js","parsejavascript.js","parsecss.js","parsexml.js","parsehtmlmixed.js"]', '["/media/dj/codemirror/css/xmlcolors.css","/media/dj/codemirror/css/jscolors.css","/media/dj/codemirror/css/csscolors.css"]' ),
    '.css':     ( u'CSS', '"parsecss.js"', '"/media/dj/codemirror/css/csscolors.css"' ),
    '.xml':     ( u'XML', '"parsexml.js"', '"/media/dj/codemirror/css/xmlcolors.css"' ),
    '.js':      ( u'JavaScript', '["tokenizejavascript.js","parsejavascript.js"]', '"/media/dj/codemirror/css/jscolors.css"' ),
    '.lua':     ( u'Lua', '"parselua.js"', '"/media/dj/codemirror/css/luacolors.css"' ),
    '.php':     ( u'PHP', '"[tokenizephp.js","parsephphtmlmixed.js"]', '"/media/dj/codemirror/css/phpcolors.css"' ),
    '.sql':     ( u'SQL', '"parsesql.js"', '"/media/dj/codemirror/css/sqlcolors.css"' ),
    #'.txt':     (),
}

editnow = ''

def sortedlistdir(path):
    dirs = sorted([d for d in os.listdir(path) if os.path.isdir(path + os.path.sep + d)])
    dirs.extend(sorted([f for f in os.listdir(path) if os.path.isfile(path + os.path.sep + f)]))
    return dirs

def escape( html ):
    if not isinstance(html, basestring): 
        html = str(html) 
    return html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'",'&#39;') 

def unescape(html): 
    "Returns the given HTML with ampersands, quotes and carets decoded" 
    if not isinstance(html, basestring): 
        html = str(html) 
    return html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;',"'") 

def djtree( project, project_id, path='', current='' ):

    curpath = os.path.join( project, path )
    if os.path.exists( curpath ):
        result = ''
        files = sortedlistdir( curpath )
        if files:
            for f in files:
                fullpath = os.path.join( curpath, f )
                relpath = os.path.join(path,f)
                relpath = replace( relpath, '\\', '/' )

                if not relpath in s.DJ_PROJECTS[int(project_id)-1]['exclude']:

                    if relpath == current:
                        sel = ' class="current"'
                    else:
                        sel = ''

                    if os.path.isdir( fullpath ):
                        icon = '/media/dj/folder.png'
                        result += '<li'+sel+'><img src="'+icon+'"/> <a href="?p='+str(project_id)+'&f='+relpath+'">'+f+'</a><ul>'+djtree( project, project_id, relpath, current )+'</ul></li>'
                        #result += 'sss'
                    else:
                        ext = os.path.splitext( f )[1]
                        icon = '/media/dj/page.png'
                        global filetypes
                        if filetypes.has_key( ext ):
                            result += '<li'+sel+'><img src="'+icon+'"/> <a href="?p='+str(project_id)+'&f='+relpath+'">'+f+'</a></li>'
            return result
    return ''

def dj( request ):

    # TODO: normal passwords
    if 'djpassword' in request.session:
        if request.session['djpassword'] != s.DJ_PASSWORD:
            error = 'password is not correct in session'
            return( render_to_response( 'dj/login.html', locals() ) )
    else:
        if (request.method == 'POST') and (u'pwd' in request.POST) and (request.POST[u'pwd'] == s.DJ_PASSWORD):
            pass
        else:
            error = 'aaaaaaaa'
            return( render_to_response( 'dj/login.html', locals() ) )

    try: 
        s.DJ_PREFIX = s.DJ_PREFIX + '' # php isset looks right?
    except AttributeError: 
        s.DJ_PREFIX = 'dj' 

    
    projects = s.DJ_PROJECTS #todo: check DJ_PROJECTS exists
    curproject = request.GET.get('p', 'none')
    if curproject != 'none':
        curpath = projects[int(curproject)-1]['path']
        curfile = request.GET.get('f', '')
        files = '<ul>'+djtree( curpath, curproject, current=curfile )+'</ul>'
        from os.path import basename
        title = basename( curfile )

        if curfile != '':
            ext = os.path.splitext( curfile ) ; ext = ext[1]
            global filetypes
            if filetypes.has_key( ext ):
                filename = os.path.join( curpath, curfile )
                
                f = open( filename, 'r')
                content = f.read().decode( 'utf-8' )
                content = escape( content )
                f.close()
                modified = os.path.getmtime( filename )
                saveurl = '/' + s.DJ_PREFIX + '/save'

                right = '\
<textarea id="codemirror">'+content+'</textarea><script> \
var editor = new CodeMirror(CodeMirror.replace("codemirror"), { \
parserfile: '+filetypes[ ext ][1]+', \
path: "/media/dj/codemirror/js/", \
stylesheet: '+filetypes[ ext ][2]+', \
content: document.getElementById("codemirror").value, \
lineNumbers:true, \
indentUnit:4, height:"100%", \
saveFunction:saveDoc\
}); var saveurl = "'+saveurl+'"; var filename = "'+curfile+'"; var project = '+curproject+'; var modified="'+str(modified)+'"; \
</script> ';

    response = render_to_response('dj/dj.html', locals() )
    request.session['djpassword'] = s.DJ_PASSWORD
    return response



def save( request ):
    #result = { 'result':'ok', 'status':'file saved', 'modified':str(newmodified) }
    #return HttpResponse( simplejson.dumps( result ), 'application/javascript; charset=utf8' )
    if request.is_ajax():
        content = request.POST.get('content') #.decode( 'utf-8' )
        #content = unescape( request.POST.get('content') )
        filename = request.POST.get('filename')
        project = request.POST.get('project')
        modified = request.POST.get('modified')
        path = s.DJ_PROJECTS[int(project)-1]['path']
        
        fullfilename = os.path.join( path, filename ) 
        if str( os.path.getmtime( fullfilename ) ) == modified:  
#BUG: todo.py
#TRY here needed and error reporting and backward copy if save failed
            from time import gmtime, strftime, localtime
            modified = strftime( '%Y%m%d-%H%M%S', localtime() )
            copyfile( fullfilename, fullfilename+'.'+modified+'.dj' )
            f = open( fullfilename, 'w')
            f.write( content.encode('utf-8') )
            #f.write( content.encode('utf-8') )
            f.close()
            newmodified = os.path.getmtime( fullfilename ) 
    
            result = { 'result':'ok', 'status':'file saved', 'modified':str(newmodified) }
        else:
            result = { 'result':'error', 'status':'file was modified by somebody' }
        
        return HttpResponse( simplejson.dumps( result ), 'application/javascript; charset=utf8' )
    else:
        return Http404
        #return HttpResponse( 'aaa' )
