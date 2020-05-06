var platform = new H.service.Platform({
    'apikey': 'u7jeE0PSCqmSBID1ynopfhCCE0626iLwV2aV4q1R_Rg'
});

// Obtain the default map types from the platform object:
var defaultLayers = platform.createDefaultLayers();

// Instantiate (and display) a map object:
var map = new H.Map(
    document.getElementById('mapContainer'),
    defaultLayers.vector.normal.map, {
        center: { lat: -37.8136, lng: 144.9631 },
        zoom: 12
    });