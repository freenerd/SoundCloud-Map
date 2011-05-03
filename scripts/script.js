var
  map,
  mapOptions = {
    mapTypeId: google.maps.MapTypeId.TERRAIN,
    center: new google.maps.LatLng(52.52760, 13.40293),
    zoom: 5,
    maxZoom: 7,
    minZoom: 3,
    disableDefaultUI: true,
    scrollwheel: false,
    zoomControl: true,
    zoomControlOptions: {
      style: google.maps.ZoomControlStyle.SMALL
    }
  },
  circleOptions = {
    fillOpacity: 0.8,
    fillColor: '#DF5D2C',
    strokeOpacity: 0,
    strokeWeight: 0,
  },
  infoWindow,
  // loading = $("#player .loading"),
  // progress = $("#player .progress"),
  // center = $('#player .center'),
  // duration = $('#player .duration'),

  sound = null,
  playerIsVisible = false,
  streamsPlayed = 0,

  siteURL = document.location.protocol + '//' + document.location.host,
  imageSiteURL = document.location.protocol + '//' + document.location.host + '/img',
  cache = new Persist.Store('TracksOnAMap');

$.facebox.settings.closeImage = '/scripts/libs/facebox/closelabel.png',
$.facebox.settings.loadingImage = '/scripts/libs/facebox/loading.gif';

function apiGet(endpoint, params, cb) {
  var uri = siteURL + '/api/' + (endpoint + '.json').replace(/\.\w+/g, '.json');
  var params = _.defaults(params || {}, {
    // consumer_key: 'FhPCTC6rJGetkMIcLwI9A',
    limit: 50,
    offset: 0
  });

  return $.getJSON(uri, params, cb);
};

var locations = (function(){
  return JSON.parse(cache.get('locations') || '{"all":[],"maxTracks":0}');
}())

locations.calcRadius = function(location) {
  var zoom = map.zoom || 5;
  var level = (map.maxZoom - zoom)  * 10000;
  return (location.track_counter / locations.maxTracks) * level + 15000;
};

locations.saveCache = function() {
  cache.set('locations', JSON.stringify(locations));
};

locations.show = function() {
  if (/\/locations\/(\w+)/.test(document.location.pathname))
    var id = _(document.location.pathname.split('/')).last();
  else if (/#locations:(\w+)/.test(document.location.hash))
    var id = _(document.location.hash.split(':')).last();

  _(locations.all).each(function(location) {
    apiGet('tracks', { location: location.id , limit: 9999999 }).done(function(tracks) {
      location.tracks = tracks;
      circles[location.id] = new google.maps.Circle(_.extend(circleOptions, {
        center: new google.maps.LatLng(location.lat, location.lon),
        radius: locations.calcRadius(location)
      }));
      circles[location.id].setMap(map);

      if (!circles[location.id].onclick) {
        circles[location.id].onclick = google.maps.event.addListener(circles[location.id], 'click', function() {
          $("#about-box").fadeOut();
          map.panTo(circles[location.id].center);
          map.panToBounds(circles[location.id].getBounds());

          if ('history' in window) {
            history.pushState({}, document.title, '/locations/' + String(location.id));
          }
          else {
            document.location.hash = '#location:' + String(location.id);
          }
          var bubble = $('#bubble-template').clone().attr('id', 'location:' + location.id);
          var bubble_html = _.template(bubble.html(), {
            location_name: location.city,
            location_tracks: location.track_counter + ' track' + (location.track_counter == 1 ? '' : 's'),
            location_link: siteURL + '/#' + location.id,
            location_twitter_share: encodeURIComponent('Enjoying the sounds of SoundCloud Meetup ' + location.city + ' on ' + siteURL + '/#' + location.id + ' #scmeetup'),
            track_title: location.tracks[0].title.substring(0, 60),
            track_avatar: _.template('<img class="avatar" src="{avatar_src}" alt="avatar">', {
              avatar_src: (location.tracks[0].artwork_url || location.tracks[0].user.avatar_url || 'images/empty.png').replace(/small|original/, 'large')
            }),
            track_artist: _.template('<a href="{user_permalink}" target="_blank">{user_name}</a>', {
              user_permalink: location.tracks[0].user.permalink_url,
              user_name: location.tracks[0].user.username
            }),
            track_time: fuzzyTime(location.tracks[0].created_at),
            track_list: _(location.tracks).map(function(track) {
              return _.template('<li id="mini{mini_track_id}" class="mini-artwork" style="background-image: url({artwork_src});"></li>', {
                mini_track_id: track.id,
                artwork_src:
                  (track.artwork_url || track.user.avatar_url || 'images/empty.png').replace(/large|original/, 'small')
              });
            }).join('')
            // city_facebook_share:
          });

          if (!!infoWindow) {
            infoWindow.close();
            google.maps.event.clearInstanceListeners(infoWindow);
          }
          infoWindow = new google.maps.InfoWindow({
            position: circles[location.id].center,
            content: '<div class="bubble">' + bubble_html + '</div>'
          });
          // google.maps.event.addListener(infoWindow, 'domready', function(){
          //   $('.avatar').live('click', function(e) {
          //     var img = $(this).attr('src').replace(/small|large/, 'original');
          //     $('.bubble:first').hide(400, function() {
          //       $(this).after(_.template('<a class="close_image" href="#" alt="Close">X</a><img src="{big_avatar}">',{
          //         big_avatar: img
          //       }));
          //       $('.close_image').live('click', function(e) {
          //         e.preventDefault();
          //         _([ $(this), $(this).next('img') ]).invoke('remove');
          //       });
          //     });
          //   });
          // });
          infoWindow.open(map);
        });

        google.maps.event.addListener(circles[location.id], 'mouseover', function() {
          circles[location.id].setOptions({ zIndex: 1E9 });
        })

        if (location.id == id || String(location.city).toLowerCase() == id)
          google.maps.event.trigger(circles[location.id], 'click');
      }
    });
  });
};


var circles = (function(){
  var circles = {};
  _(locations.all).each(function(location) {
    circles[location.id] = new google.maps.Circle(_.extend(circleOptions, {
      center: new google.maps.LatLng(location.lat, location.lon),
      radius: locations.calcRadius(location)
    }))
  });
  return circles;
}());

_.templateSettings = {
  interpolate : /\{(.+?)\}/g
};

map = new google.maps.Map($('#map_canvas')[0], mapOptions);

$("#map_canvas").height($(window).height());

$(window).resize(function() {
  $("#map_canvas").height($(window).height() - (playerIsVisible ? PLAYER_HEIGHT : 0));
  google.maps.event.trigger(map, 'resize');
});

 // about box closable
$("#about-box a.close").click(function(ev) {
  ev.preventDefault();
  $("#about-box").fadeOut();
});

// about box openable
$("a#about").click(function(ev) {
  ev.preventDefault();
  $("#about-box").fadeIn();
});

// about box closes when action on map
_([ 'dragstart', 'click', 'zoom_changed' ]).each(function(ev) {
  google.maps.event.addListener(map, ev, function() {
    $("#about-box").fadeOut();
  });
});

google.maps.event.addListener(map, 'zoom_changed', function() {
  _(locations.all).each(function(location) {
    circles[location.id].setRadius(locations.calcRadius(location));
  });
})

google.maps.event.addListenerOnce(map, 'idle', function() {
  setInterval(locations.saveCache, 10000) // Save cache in a 10 seconds interval
  window.onunload = document.onunload = locations.saveCache;

  // Remember created_at and duration
  if (locations.all.length == 0) {
    $.when(
      apiGet('locations', { offset: 0   }),
      apiGet('locations', { offset: 50  }),
      apiGet('locations', { offset: 100 }),
      apiGet('locations', { offset: 150 }),
      apiGet('locations/maxtracks')
    ).done(function(locations1, locations2, locations3, locations4, maxtracks) {
      locations.all = _([ locations1, locations2, locations3, locations4 ]).chain().pluck('0').flatten().compact().value(),
      locations.maxTracks = maxtracks[0].max_tracks;
      locations.show();
    })
  }
  else {
    locations.show();
  }
});

// display a human readable time
function fuzzyTime(date_str){
  var time_formats = [
    [60, 'just now', 1], // 60
    [120, '1 minute ago', '1 minute from now'], // 60*2
    [3600, 'minutes', 60], // 60*60, 60
    [7200, '1 hour ago', '1 hour from now'], // 60*60*2
    [86400, 'hours', 3600], // 60*60*24, 60*60
    [172800, 'yesterday', 'tomorrow'], // 60*60*24*2
    [604800, 'days', 86400], // 60*60*24*7, 60*60*24
    [1209600, 'last week', 'next week'], // 60*60*24*7*4*2
    [2419200, 'weeks', 604800], // 60*60*24*7*4, 60*60*24*7
    [4838400, 'last month', 'next month'], // 60*60*24*7*4*2
    [29030400, 'months', 2419200], // 60*60*24*7*4*12, 60*60*24*7*4
    [58060800, 'last year', 'next year'], // 60*60*24*7*4*12*2
    [2903040000, 'years', 29030400], // 60*60*24*7*4*12*100, 60*60*24*7*4*12
    [5806080000, 'last century', 'next century'], // 60*60*24*7*4*12*100*2
    [58060800000, 'centuries', 2903040000] // 60*60*24*7*4*12*100*20, 60*60*24*7*4*12*100
  ];
  var time = ('' + date_str).replace(/-/g,"/").replace(/[TZ]/g," ").replace(/^\s\s*/, '').replace(/\s\s*$/, '');
  if(time.substr(time.length-4,1)==".") time =time.substr(0,time.length-4);
  var seconds = (new Date - new Date(time)) / 1000;
  var token = 'ago', list_choice = 1;
  if (seconds < 0) {
    seconds = Math.abs(seconds);
    token = 'from now';
    list_choice = 2;
  }
  var i = 0, format;
  while (format = time_formats[i++])
    if (seconds < format[0]) {
      if (typeof format[2] == 'string')
        return format[list_choice];
      else
        return Math.floor(seconds / format[2]) + ' ' + format[1] + ' ' + token;
    }
  return time;
};


// main keyboard listener
// $(window).keydown(function(ev) {
//   if(ev.keyCode === 32) { // start/stop play
//     togglePlay();
//   } else if (ev.keyCode === 39) { // arrow next, play next if playing
//     stop();
//     playRandom();
//   } else if (ev.keyCode === 37) { // arrow prev, play prev if playing
//     // not implemented
//   }
// });

// show about box
$("#about-box").fadeIn();

// show about box, if on live server and user hasn't seen it for 24 hours
// if(location.href.split(".").length > 1 && !$.cookie('viewed_intro') == '1'){
//// if(!$.cookie('viewed_intro') == '1'){
//  $.cookie('viewed_intro', '1', { expires: 1 });
//  $("#about-box").fadeIn();
//}

// start the app, then play a random track
// loadLocations(maxApiUrl, deepApiUrl, tracksUrl, function() {
//   playRandom();
// });

//pop up the track that was shared if /#track-123123 detected
// if(location.hash && location.hash.search(/track|city/) != -1) {
//   var id = location.hash.split("-")[1];
//   var q = "/api/tracks/";
//   if(location.hash.search(/track/) != -1) { // track permalink
//     q += id;
//   } else if(location.hash.search(/city/) != -1) { // location permalink
//     q += "?limit=1&location="+ id;
//   }
//   $.getJSON(q,function(track) {
//     showPlayer(track[0]);
//     map.setZoom(5);
//     setupLocation(track[0].location,track[0].id);
//     GEvent.trigger(locations[locations.length-1].circle,'click'); // play the track (is this really clean?)
//   });
// }
//
// if(location.hash && location.hash.search(/scconnect/) != -1) {
// var q = "/api/soundcloud-connect/followers/";
// $.getJSON(q,function(location) {
//   $.each(location,function(i,l) {
//     setupLocation(l);
//     });
//   });
// }
