mapboxgl.accessToken = 'pk.eyJ1IjoiZGhlbnJ5NDM3IiwiYSI6ImNrOXY3cjUxNjA5cDQzZHBrc2w1N3M4em4ifQ.hzae72u-br3ad-rYz_2h2g';

var placeResult;

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11', //'mapbox://styles/dhenry437/ck9v860rb00dp1inpfefyxgww'
    center: { lat: -37.8136, lng: 144.9631 },
    zoom: 12,
    keyboard: true
});

map.addControl(
    new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        mapboxgl: mapboxgl,
        collapsed: true
    })
);

// Add zoom and rotation controls to the map.
map.addControl(new mapboxgl.NavigationControl());

// Add geolocate control to the map.
map.addControl(
    new mapboxgl.GeolocateControl({
        positionOptions: {
            enableHighAccuracy: true
        },
        trackUserLocation: true
    })
);

// Geocoder for add review modal
var geocoder = new MapboxGeocoder({
    accessToken: mapboxgl.accessToken
});

geocoder.addTo('#addReviewPlace');

// Check if place exits in db
geocoder.on('result', function(e) {
    // console.log("geocoder");
    // console.log(e);

    placeResult = e;
});

$.ajax({
    url: "places",
    method: "GET",
    success: function(data) {
        data.places.forEach(place => {
            new mapboxgl.Marker()
                .setLngLat([place.lat, place.lon])
                .setPopup(new mapboxgl.Popup()
                    .setHTML(`<h5>${place.name}</h5><p>${place.streetAddress}, ${place.suburb}<br>${place.state} ${place.postCode}, ${place.country}</p><button id="btnPlace" class="btn btn-primary" onclick="showPlacesModal('${place.id}','${place.name}','${place.streetAddress}','${place.suburb}','${place.state}','${place.postCode}','${place.country}')">Reviews</button>`))
                .addTo(map);
        });
    },
});

function showPlacesModal(id, name, streetAddress, suburb, state, postCode, country) {
    $("#placesModalName").text(name);
    $("#placesModalAddress").text(`${streetAddress}, ${suburb}, ${state} ${postCode}, ${country}`);
    $("#placeId").text(id);

    $('#placesModal').modal('show');

    // Load reviews
    loadReviews(id);
}