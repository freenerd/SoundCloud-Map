soundManager.flashVersion = 9;
soundManager.useHTML5Audio = true;
soundManager.useConsole = false;
soundManager.consoleOnly = false;
soundManager.debugMode = false;
soundManager.defaultOptions.multiShot = false;
soundManager.allowPolling = true;
soundManager.useFastPolling = true;
soundManager.useHighPerformance = true;
soundManager.url = "/scripts/soundmanager2_flash9.swf";

soundManager.onready(function(){

  if (/\/locations\/([\w-]+)/.test(document.location.pathname)) {
   var components =  _(document.location.pathname.split('/')).last().split('-');
  }
  else if (/#locations:([\w-]+)/.test(document.location.hash)) {
    var components =  _(document.location.hash.split(':')).last().split('-');
  }

  if (!!components) {
    var currentLocationId = _(components).first();
    var currentTrackId = components.length > 1 ? components[1] : undefined;
  }


  var mapOptions = {
    mapTypeId: google.maps.MapTypeId.TERRAIN,
    zoom: 3,
    center: new google.maps.LatLng(62, -30),
    minZoom: 3,
    maxZoom: 7,
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
  siteURL = document.location.protocol + '//' + document.location.host,
  imageSiteURL = document.location.protocol + '//' + document.location.host + '/img';

  var apiGet = function(endpoint, params, cb) {
    var uri = siteURL + '/api/' + (endpoint + '.json').replace(/\.\w+/g, '.json');
    var params = _.defaults(params || {}, {
      // consumer_key: 'FhPCTC6rJGetkMIcLwI9A',
      limit: 50,
      offset: 0
    });

    return $.getJSON(uri, params, cb);
  };

  var avatar = {
    format: function(img, format) {
      var formats = [
        't500x500', //   => '500x500^'
        't300x300', //   => '300x300^'
        'crop',     //   => '400x400'
        'large',    //   => '100x100^'
        'badge',    //   => '47x47^'
        'small',    //   => '32x32^'
        'tiny',     //   => '18x18^'
        'mini',     //   => '16x16^'
        'original'
      ];

      return formats.indexOf(format) > -1 ?
               img.replace(new RegExp(formats.join('|'), 'g'), format) :
               img;
    },

    for_track: function(track, format) {
      var avatar_url = track.artwork_url || track.user.avatar_url || '/images/empty.png';
      return avatar.format(avatar_url, format);
    }
  };

  _.templateSettings = {
    interpolate : /\{(.+?)\}/g
  };

  var locations = {
    all: [],
    maxTracks: 0
  };

  var circles = {};
  var bubble;

  locations.shareURL = function(location, track) {
    var url = !!location ? siteURL + '/locations/' + location.id : undefined;
    if (!!url && !!track) url += ('-' + track.id);
    return url;
  };

  locations.twitterShareURL = function(location, track) {
    if (!!location)
      return _.template("http://twitter.com/home?source=soundcloudmeetupmap&status={status}", {
        status: encodeURIComponent(_.template('Enjoying the sounds of SoundCloud Meetup {city} on {share_url} #scmeetup', {
          city: location.city || location.country,
          share_url: locations.shareURL(location, track)
        }))
      })
  };

  locations.facebookShareURL = function(location, track) {
    if (!!location)
      return _.template("http://www.facebook.com/share.php?u={link}&t={status}", {
        link: encodeURIComponent(siteURL + "/from-facebook?type=city&id=" + location.id),
        status: encodeURIComponent(_.template('Enjoying the sounds of SoundCloud Meetup {city} on {share_url} #scmeetup', {
          city: location.city || location.country,
          share_url: locations.shareURL(location, track)
        }))
      })
  };

  locations.calcRadius = function(location) {
    var zoom = (!!map && map.zoom) || mapOptions.zoom;
    var level = (mapOptions.maxZoom - zoom)  * 15000;
    return (location.track_counter / locations.maxTracks) * level + 15000;
  };

  locations.find = function(id) {
    return _(locations.all).detect(function(loc) {
      return loc.id == id;
    });
  };

  locations.show = function() {
    _(circles).invoke('setMap', null);
    circles = {};

    _(locations.all).each(function(location) {
      apiGet('tracks', { location: location.id , limit: 9999999 }).done(function(tracks) {
        location.tracks = {};
        _(tracks).each(function(track) {
          location.tracks[track.id] = track;
        });

        circles[location.id] = new google.maps.Circle(_.extend(circleOptions, {
          center: new google.maps.LatLng(location.lat, location.lon),
          radius: locations.calcRadius(location)
        }));
        circles[location.id].setMap(map);

        google.maps.event.addListener(circles[location.id], 'click', function() {
          $("#about-box").fadeOut();
          map.panTo(circles[location.id].center);

          if ('history' in window)
            history.pushState({}, document.title, '/locations/' + String(location.id));
          else
            document.location.hash = '#location:' + String(location.id);

          var track = location.tracks[ _(location.tracks).keys()[0] ];
          var bubble_html = $('#bubble-template').clone();
          bubble_html.find('.city-track-counter').html(location.track_counter + ' track' + (location.track_counter == 1 ? '' : 's')).end()
                     .find('.city-name').html(location.city).end()
                     .find('.share-on-twitter').html(locations.twitterShareURL(location, track)).end()
                     .find('.share-on-facebook').html(locations.facebookShareURL(location, track)).end()

          $(document).trigger('updateBubble', track);

          if (!!bubble) {
            bubble.close();
            google.maps.event.clearInstanceListeners(bubble);
          }
          bubble = new google.maps.InfoWindow({
            position: circles[location.id].center,
            content: '<div class="bubble active">' + bubble_html.html() + '</div>'
          });

          google.maps.event.addListener(bubble, 'domready', function() {
            if (player.data.location != location) {
              if(!!currentTrackId) {
                player.load(location, currentTrackId);
                currentTrackId = undefined;
              }
              else
                player.load(location);
            }

            $(document).trigger('updateBubble', player.data.location.tracks[ player.data.current ]);

            $('.mini-artwork').live('click', function(e) {
              e.preventDefault();
              player.load(player.data.location, $(this).attr('id').replace('mini', ''))
            });

            $('.avatar').live('click', function(e) {
              var image = new Image();
              var old_content = $('.bubble').html();
              var reverse = function() {
                bubble.setContent('<div class="bubble active">' + old_content + '</div>');
                bubble.open(map);
              };
              image.onclick = reverse;
              image.onload = function() {
                bubble.setContent(image);
              };
              image.src = avatar.format($(this).attr('src'), 't300x300');
            });
          });

          // google.maps.event.addListener(circle, 'mouseover', function() {
          //   circles.setOptions({ zIndex: 1E9 });
          // })

          bubble.open(map);
          map.panToBounds(circles[location.id].getBounds());
        });

        if (location.id == currentLocationId)
          setTimeout(function() {
            google.maps.event.trigger(circles[location.id], 'click');
          }, 500);

      });
    });
  };

  player = {
    nodes: {
      container: $('#player-container'),
      player: $('#player'),
      loading: $("#player .loading"),
      progress: $("#player .progress"),
      center: $('#player .center'),
      duration: $('#player .duration'),
      waveform: $('#player .waveform')
    },
    sound: undefined,
    play: function() {
      if (player.sound === undefined) return;
      else player.sound.paused ? player.sound.resume() : player.sound.play();
    },
    pause: function() {
      if (player.sound === undefined) return;
      else player.sound.pause();
    },
    toggle: function() {
      if (player.sound === undefined) return;
      else player.sound.togglePause();
    },
    seek: function(e) {
      if (player.sound === undefined) return;
      else {
        e.preventDefault();
        var percent = (e.clientX - player.nodes.waveform.offset().left) / (player.nodes.waveform.width());
        if(player.sound.durationEstimate * percent < player.sound.durationEstimate)
          player.sound.setPosition(player.sound.durationEstimate * percent);
      }
    }
  };

  player.init = function() { // Run only once
    player.init.initialized = player.init.initialized || false;
    if (player.init.initialized) return;
    player.data = {};
    player.nodes.player.find('.prev').click(player.previous);
    player.nodes.player.find('.pause').click(player.toggle);
    player.nodes.player.find('.next').click(player.next);
    player.nodes.player.find('.waveform').click(player.seek);
    player.init.initialized = true;
  };

  player.load = function(location, current) {
    if (!current || current < 0)
      var current = _(location.tracks).keys()[0];

    if (!location.tracks[current]) return;

    if (!player.nodes.container.is(':visible')) {
      player.nodes.container.slideDown('fast');
      $(document).trigger('forceResize');
    }

    if (!!player.data.location && player.data.location.id == location.id && !!player.data.current && player.data.current == current)
      return;
    else
      player.data = {
        location: location,
        current: current
      };

    window.soundManager.stopAll();

    var track = player.data.location.tracks[ player.data.current ];
    $(document).trigger('updateBubble', track);
    $(document).trigger('updatePlayer', track);

    player.sound = soundManager.createSound({
      id: track.id,
      url: track.stream_url + "?consumer_key=FhPCTC6rJGetkMIcLwI9A",
      whileloading: function() {
        player.nodes.loading.css('width', (player.sound.bytesLoaded / player.sound.bytesTotal) * 100 + '%');
      },
      whileplaying: function() {
        player.nodes.progress.css('width', (player.sound.position / track.duration) * 100 + '%');
        player.nodes.player.find('.position').html(formatMs(player.sound.position));
        player.nodes.duration.html(formatMs(track.duration));
      },
      onfinish: function() {
        $('body').removeClass('playing');
        player.next()
      },
      onload: function(loaded) {
        player.nodes.loading.css('width', '100%');
      },
      onplay: function() {
        $('body').addClass("playing");
        $(document).trigger('updateBubble', player.data.location.tracks[ player.data.current ]);
      },
      onresume: function() {
        $('body').addClass("playing");
      },
      onpause: function() {
        $('body').removeClass("playing");
      }
    });

    if(player.sound.bytesLoaded == player.sound.bytesTotal)
      player.nodes.loading.css('width',"100%");

    player.play();

  };

  player.previous = function() {
    if (!player.data) return;
    var ids = _(player.data.location.tracks).keys();
    var track_id = ids[ ids.indexOf(player.data.current) - 1 ];
    !!track_id && player.load(player.data.location, track_id);
  };

  player.next = function() {
    if (!player.data) return;
    var ids = _(player.data.location.tracks).keys();
    var track_id = ids[ ids.indexOf(player.data.current) + 1 ];
    !!track_id && player.load(player.data.location, track_id);
  };

  if (!!circles[currentLocationId] && circles[currentLocationId].center)
    var map = new google.maps.Map($('#map_canvas')[0], _.extend(mapOptions, {
      center: circles[currentLocationId].center
    }));
  else
    var map = new google.maps.Map($('#map_canvas')[0], mapOptions);

  $(document).bind('forceResize', function(e) {
    $("#map_canvas").height($(window).height() - (player.nodes.container.is(':visible') ? player.nodes.container.height() : 0))
    google.maps.event.trigger(map, 'resize');
  });

  $(document).bind('updateBubble', function(e) {
    var track = _(arguments).last();
    var bubble_html = $('.bubble.active');
    bubble_html.find('.artwork').html(_.template('<img class="avatar" src="{avatar_src}" alt="avatar">', {
      avatar_src: avatar.for_track(track, 'large')
    })).end()
               .find('.title').html(_.template('<a href="{track_permalink}" target="_blank">{track_title}</a>', {
                  track_permalink: track.permalink_url,
                  track_title: track.title
                })).end()
               .find('.artist').html(_.template('<a href="{user_permalink}" target="_blank">{user_name}</a>', {
                  user_permalink: track.user.permalink_url,
                  user_name: track.user.username
               })).end()
               .find('.time').html(fuzzyTime(track.created_at)).end();
    var mini_container = bubble_html.find('.tracks-list');

    if (mini_container.find('.mini-artwork').length == 0) {
      mini_container.append(_.map(_(locations.find(track.location.id).tracks).values().slice(0, 20), function(minitrack) {
        return _.template('<li id="mini{mini_track_id}" class="mini-artwork" style="background-image: url({artwork_src});"></li>', {
          mini_track_id: minitrack.id,
          artwork_src: avatar.for_track(minitrack, 'small')
        });
      }).join(''))
      var current_index = mini_container.find('#mini' + track.id).addClass('active').index() / 10 | 0;
    }
    else {
      var last_index = mini_container.find('.mini-artwork.active').removeClass('active').index() / 10 | 0;
      var current = bubble_html.find('#mini' + track.id).addClass('active');
      var current_index = current.index() / 10 | 0;
      if (current_index > last_index) {
        var location = locations.find(track.location.id);
        var track_ids = _(location.tracks).keys();
        var from = track_ids.indexOf(mini_container.find('.mini-artwork:last').attr('id').replace('mini', ''));
        var to = from + (!!track_ids[ from + 20 ] ? 20 : (track_ids.length - 1 - from));
        var next_20_tracks = _(location.tracks).values().slice(from, to);
        mini_container.append(_(next_20_tracks).map(function(minitrack) {
          return _.template('<li id="mini{mini_track_id}" class="mini-artwork" style="background-image: url({artwork_src});"></li>', {
            mini_track_id: minitrack.id,
            artwork_src: avatar.for_track(minitrack, 'small')
          });
        }).join(''));
      }
    }
    mini_container.stop().animate({
      "scrollTop": 36 * current_index
    }, 300);
  });

  $(document).bind('updatePlayer', function(e) {
    var track = _(arguments).last();
    // set up share to twitter, no url shortener yet
    // var twitterShareLink = "I found " + track.title  + " by " + track.user.username + " on " + linkToBeShared + " #scmeetup";
    // twitterShareLink = "http://twitter.com/home/?source=scmeetupmap&status=" + encodeURIComponent(twitterShareLink);
    player.nodes.container.find('.share-on-twitter').attr('href', locations.twitterShareURL(location));

    // set up share to Facebook
    // var facebookLinkToBeShared = siteURL + "/from-facebook?type=track&id=" + track.id
    // var facebookShareLink = "SoundCloud Meetup Day " + track.location.city + ": " + track.title  + " by " + track.user.username;
    // facebookShareLink = "http://www.facebook.com/share.php?u=" + encodeURIComponent(facebookLinkToBeShared) + "&t=" + encodeURIComponent(facebookShareLink);
    player.nodes.container.find('.share-on-facebook').attr('href', locations.facebookShareURL(location));

    var tmpl = '<a target="_blank" href="{track_permalink_url}">{track_title}</a> uploaded by ' +
               '<a target="_blank" href="{user_permalink_url}">{user_name}</a>';

    player.nodes.container.find('.metadata .metadata-html').html(_.template(tmpl, {
      track_permalink_url: track.permalink_url,
      track_title: track.title,
      user_permalink_url: track.user.permalink_url,
      user_name: track.user.username
    }));

    player.nodes.waveform.find('img').animate({ opacity: 0 }, 150, function() {
      $(this).attr('src', track.waveform_url).animate({ opacity: 1 }, 150);
    })
  });

  $(window).resize(function() {
    $(document).trigger('forceResize');
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

  google.maps.event.addListenerOnce(map, 'idle', function() {

    $(document).trigger('forceResize');
    player.init();
    $("#about-box").fadeIn();


    $(window).keyup(function(e) {
      var actions = {
        82: function() { // R: Random location!
          google.maps.event.trigger(circles[ locations.all[Math.floor(Math.random() * locations.all.length)].id ], 'click');
        },
        67: function() { // C: Center and open bubble for closest location
          var closest = _(circles).min(function(circle) {
            return google.maps.geometry.spherical.computeDistanceBetween(map.getCenter(), circle.center)
          });
          !closest.getBounds().contains(map.getCenter()) && google.maps.event.trigger(closest, 'click');
        },
        37: player.previous,
        32: player.toggle,
        39: player.next
      };
      actions.hasOwnProperty(e.keyCode) && actions[e.keyCode].call();
    });

    // Remember created_at and duration
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
      if (!currentLocationId) {
        if (!!navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(function(position) {
            var center = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
            var meetup = _(circles).detect(function(circle) {
              return circle.getBounds().contains(center);
            });
            if (!!meetup){
              google.maps.event.trigger(meetup, 'click');
              // google.maps.event.trigger(infoWindow, 'content_changed');
            }
          }, function(err) {});
        }
      }
    })
  });


  function formatMs(ms) {
    var s = Math.floor((ms/1000) % 60);
    if (s < 10) { s = "0"+s; }
    return Math.floor(ms/60000) + "." + s;
  }

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
});
