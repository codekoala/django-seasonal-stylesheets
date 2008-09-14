from django.db import models
from django.db.models import Q
from django.core.urlresolvers import reverse
from datetime import date, datetime, timedelta

class SeasonalStylesheet(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    template_name = models.CharField(max_length=200, help_text='By default, this will be dsss/[slug].css', blank=True)
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('dsss-stylesheet', kwargs={'slug': self.slug})
    
    def __template(self):
        if self.template_name:
            return self.template_name
        return 'dsss/%s.css' % self.slug
    template = property(__template)
    
    def __last_updated(self):
        """
        Determines the most recent date and time any of this stylesheet's
        seasons was changed.
        """
        last = None
        for s in self.seasons.all():
            if not last or last < s.date_updated:
                last = s.date_updated
        return last
    last_updated = property(__last_updated)
    
    class Meta:
        ordering = ['name']

class Color(models.Model):
    stylesheet = models.ForeignKey(SeasonalStylesheet, related_name='variables')
    variable_name = models.SlugField(help_text='This must be a valid Python variable name (i.e., no dashes, spaces, or other non-alphanumeric characters)')
    
    def __unicode__(self):
        return self.variable_name

class SeasonManager(models.Manager):
    def current(self, stylesheet, today=None):
        """
        A current season is one that is closest to today, but in the past.
        The next season is closest to today but in the future.  The term
        "closest" is evaluated by both month and day (but not year).
        """
        current = next = smallest = largest = None
        today = today or date.today()
        day_of_year = int(today.strftime('%j'))
        
        # get all seasons associated with the specified stylesheet
        seasons = self.get_query_set().filter(stylesheet=stylesheet)
        
        # run thru all seasons once to find the first and last season of a year
        for s in seasons:
            doy = int(s.season_date.strftime('%j'))
            if not smallest or doy < int(smallest.season_date.strftime('%j')):
                smallest = s
            if not largest or doy > int(largest.season_date.strftime('%j')):
                largest = s
        
        # run thru again to get the most recently past season
        for s in seasons:
            doy = int(s.season_date.strftime('%j'))
            if not current and doy <= day_of_year:
                current = s
            if not next and doy > day_of_year:
                next = s

            if doy <= day_of_year:
                if day_of_year - doy < day_of_year - int(current.season_date.strftime('%j')):
                    current = s
            elif doy > day_of_year:
                if doy - day_of_year < int(next.season_date.strftime('%j')) - day_of_year:
                    next = s
        
        if not current:
            current = largest
        if not next:
            next = smallest
        
        return current, next

class Season(models.Model):
    stylesheet = models.ForeignKey(SeasonalStylesheet, related_name='seasons')
    name = models.CharField(max_length=50)
    season_date = models.DateField(help_text='Choose the date this season is in full-swing')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    objects = SeasonManager()
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['season_date', 'name']

class SeasonColor(models.Model):
    season = models.ForeignKey(Season, related_name='colors')
    variable = models.ForeignKey(Color)
    value = models.CharField(max_length=6, help_text='The hexadecimal color code (without the #) to use when this season is in full-swing')
    
    def __unicode__(self):
        return u'%s in %s (#%s)' % (self.variable, self.season, self.value)

