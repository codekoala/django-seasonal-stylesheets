from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.template import loader, Context
from django.conf import settings
from dsss.models import SeasonalStylesheet, Season, SeasonColor
from datetime import date, datetime
import os

# see if the user has overridden the 'save to file' option
if hasattr(settings, 'DSSS_SAVE'):
    STORE = settings.DSSS_SAVE
else:
    STORE = True

def get_stylesheet(request, name, year, month, day):
    year, month, day = int(year), int(month), int(day)
    modified = None
    today = date(year, month, day)
    sheet = get_object_or_404(SeasonalStylesheet, slug=name)

    # see if the stylesheet already exists on the filesystem
    filename = '%s-%i-%02i-%02i.css' % (name, year, month, day)
    path = os.path.join(settings.MEDIA_ROOT, 'dsss', 'stylesheets')
    output = os.path.join(path, filename)
    
    if STORE:
        # make sure the path exists
        try:
            os.makedirs(path)
        except OSError:
            pass

        # determine the modification date of the sheet
        try:
            modified = datetime.fromtimestamp(os.path.getmtime(output))
        except OSError:
            pass

    # see if the file was last modified before the stylesheet
    if not modified or (modified and modified < sheet.last_updated):
        create = True
    else:
        create = False
    
    if not create and STORE:
        # everything should be fine, let's just output the file's contents
        f = open(output, 'r')
        content = f.read()
        f.close()
    else:
        template = loader.get_template(sheet.template)
        
        current, next = Season.objects.current(sheet, today)
        if not current or not next:
            raise Http404
        
        # determine how many days there are between the current and next seasons
        tdoy = int(today.strftime('%j'))
        cdoy = int(current.season_date.strftime('%j'))
        ndoy = int(next.season_date.strftime('%j'))
        if cdoy <= ndoy:
            days = ndoy - cdoy
            diff = tdoy - cdoy
        elif ndoy < cdoy:
            days = 365 - cdoy + ndoy
            if tdoy > cdoy:
                diff = tdoy - cdoy
            else:
                diff = 365 - cdoy + tdoy
        
        # make days a float for a little more accruacy
        days += 0.0

        data = {}
        for cc in current.colors.all():
            varname = cc.variable.variable_name
            try:
                nc = next.colors.get(variable=cc.variable)
            except SeasonColor.DoesNotExist:
                data[varname] = cc.value
            else:
                # current red, green, and blue hex codes
                cr, cg, cb = cc.value[:2], cc.value[2:4], cc.value[4:]
                cr, cg, cb = int(cr, 16), int(cg, 16), int(cb, 16)
                
                # next red, green, and blue hex codes
                nr, ng, nb = nc.value[:2], nc.value[2:4], nc.value[4:]
                nr, ng, nb = int(nr, 16), int(ng, 16), int(nb, 16)
             
                if cdoy == tdoy:
                    data[varname] = '#' + cc.value
                else:
                    # reds
                    rdiff = (nr - cr) / days
                    red = cr + int(rdiff * diff) # round off decimal places
                    if red > 255:
                        red %= 255
                    
                    # greens
                    gdiff = (ng - cg) / days
                    green = cg + int(gdiff * diff) # round off decimal places
                    if green > 255:
                        green %= 255
                    
                    # blues
                    bdiff = (nb - cb) / days
                    blue = cb + int(bdiff * diff) # round off decimal places
                    if blue > 255:
                        blue %= 255

                    data[varname] = 'rgb(%i, %i, %i)' % (red, green, blue)
                    #raise Exception()
        
        context = Context(data)
        content = template.render(context)
        
        # only create the files when required
        if STORE:
            f = open(output, 'w')
            f.write(content)
            f.close()

    return HttpResponse(content, mimetype='text/css')
    
