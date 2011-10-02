"""
Utilities for loading boundaries into our Geodjango database.
"""
import gc
import os
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping

# The location of this directory
this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir, 'data')
# The location of our source files.
shp_file = os.path.join(data_dir, 'tl_2010_us_state10.shp')
pop_file = os.path.join(data_dir, 'population.csv')


def all():
    """
    Wrap it all together and load everything
    
    Example usage:
        
        >> from us_states import load; load.all();

    """
    from models import State
    [i.delete() for i in State.objects.all()]
    shp()
    extras()


def shp():
    """
    Load the ESRI shapefile from the Census in the County model.
    
    Example usage:
    
        >> from us_states import load; load.shp();
    
    """
    # Import the database model where we want to store the data
    from models import State
    
    # A crosswalk between the fields in our database and the fields in our
    # source shapefile
    shp2db = {
        'polygon_4269': 'Polygon',
        'fips_code': 'STATEFP10',
        'name': 'NAME10',
        'usps_code': 'STUSPS10',
    }
    # Load our model, shape, and the map between them into GeoDjango's magic
    # shape loading function (I also slipped the source coordinate system in
    # there. The Census says they put everything in NAD 83, which translates
    # to 4269 in the SRID id system.)
    lm = LayerMapping(State, shp_file, shp2db, source_srs=4269, encoding='latin-1')
    # Fire away!
    lm.save(verbose=False)


def population():
    """
    Load the populations using the FIPS codes as our guide.
    """
    import csv
    r = csv.DictReader(open(pop_file, 'r'))
    d = {}
    for i in r:
        d[i.get('STATE_OR_REGION')] = i.get('2010_POPULATION')
    return d


def extras():
    """
    Load some of the extra data we want for our model that's not included
    in the source shapefile. 
        
        * The Django state field
        * The slug field
        * The ForeignKey connection to a State model.
        * Simplified versions of our polygons that contain few points
        
    Example usage:
    
        >> from us_states import load; load.extras();
        
    """
    from django.template.defaultfilters import slugify
    from models import State
    # Pull a crosswalk between FIPS and populations
    pdict = population()
    # Loop through everybody...
    for obj in queryset_iterator(State.objects.all()):
        # ...set the state...
        obj.population = pdict[obj.name]
        # ...slug...
        obj.slug = slugify(obj.name)
        # .. the full set of polygons...
        obj.set_polygons()
        # ... the square miles ...
        obj.square_miles = obj.get_square_miles()
        # ... is_state ..
        if obj.name in ['District of Columbia', 'Puerto Rico']:
            obj.is_state = False
        else:
            obj.is_state = True
        # ... save the changes ...
        obj.save()
    # ... and then loop again to set the simple polygons to avoid a weird bug
    # I've had when I do them right after the polygons.
    for obj in queryset_iterator(State.objects.all()):
        obj.set_simple_polygons()
        obj.save()


def queryset_iterator(queryset, chunksize=100):
    """
    Iterate over a Django Queryset ordered by the primary key
    
    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.
    
    Note that the implementation of the iterator does not support ordered query sets.
    
    Lifted from: http://www.mellowmorning.com/2010/03/03/django-query-set-iterator-for-really-large-querysets/
    """
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()


def specs():
    """
    Examine our source shapefile and print out some basic data about it.
    
    We can use this to draft the model where we store it in our system.
    
    Done according to documentation here: http://geodjango.org/docs/layermapping.html
    
    Example usage:
    
        >> from us_states import load; load.specs();
    
    What we get in this case:
    
        Fields: ['REGION10', 'DIVISION10', 'STATEFP10', 'STATENS10', 'GEOID10', 
        'STUSPS10', 'NAME10', 'LSAD10', 'MTFCC10', 'FUNCSTAT10', 'ALAND10', 
        'AWATER10', 'INTPTLAT10', 'INTPTLON10']
        Number of features: 52
        Geometry Type: Polygon
        SRS: GEOGCS["GCS_North_American_1983",
            DATUM["North_American_Datum_1983",
                SPHEROID["GRS_1980",6378137,298.257222101]],
            PRIMEM["Greenwich",0],
            UNIT["Degree",0.017453292519943295]]
    """
    # Crack open the shapefile
    ds = DataSource(shp_file)
    # Access the data layer
    layer = ds[0]
    # Print out all kinds of goodies
    print "Fields: %s" % layer.fields
    print "Number of features: %s" % len(layer)
    print "Geometry Type: %s" % layer.geom_type
    print "SRS: %s" % layer.srs


