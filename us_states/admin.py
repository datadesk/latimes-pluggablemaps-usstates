# Admin
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

# Models
from us_states.models import State


class StateAdmin(OSMGeoAdmin):
    list_display = ('name', 'is_state')
    list_filter = ('is_state',)
    search_fields = ('name',)
    fieldsets = (
        (('Boundaries'),
            {'fields': ('polygon_4269', ),
             'classes': ('wide',),
            }
        ),
        (('Description'),
           {'fields': (
                'name', 'slug', 'square_miles', 'population'),
            'classes': ('wide',),
           }
        ),
        (('ID Codes'),
           {'fields': (
                'fips_code', 'usps_code'),
            'classes': ('wide',),
           }
        ),
     )
    readonly_fields = (
        'name', 'slug', 'square_miles',
        'fips_code', 'usps_code', 'population',
        )
    layerswitcher = False
    scrollable = False
    map_width = 400
    map_height = 400
    modifiable = False

admin.site.register(State, StateAdmin)
