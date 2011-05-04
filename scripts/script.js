soundManager.flashVersion = 9;
soundManager.useHTML5Audio = true;
soundManager.useConsole = false;
soundManager.consoleOnly = false;
soundManager.debugMode = false;
soundManager.defaultOptions.multiShot = false;
soundManager.url = "/scripts/soundmanager2_flash9.swf";

soundManager.onready(function(){
  if (/\/locations\/(\w+)/.test(document.location.pathname))
    var id = _(document.location.pathname.split('/')).last();
  else if (/#locations:(\w+)/.test(document.location.hash))
    var id = _(document.location.hash.split(':')).last();

  var mapOptions = {
    mapTypeId: google.maps.MapTypeId.TERRAIN,
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
  siteURL = document.location.protocol + '//' + document.location.host,
  imageSiteURL = document.location.protocol + '//' + document.location.host + '/img',
  cache = new Persist.Store('TracksOnAMap');

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

  var locations = (function(){
    return JSON.parse(cache.get('locations') || '{"all":[],"maxTracks":0}');
  }());

  locations.shareURL = function(location) {
    return !!location ? siteURL + '/locations/' + location.id : undefined;
  };

  locations.twitterShareURL = function(location) {
    if (!!location)
      return _.template("http://twitter.com/?source=soundcloudmeetupmap&status={status}", {
        status: _.template('Enjoying the sounds of SoundCloud Meetup {city} on {share_url} #scmeetup', {
          city: encodeURIComponent(location.city || location.country),
          share_url: encodeURIComponent(locations.shareURL(location))
        })
      })
  };

  locations.facebookShareURL = function(location) {
    if (!!location)
      return _.template("http://www.facebook.com/share.php?u={link}&t={status}", {
        link: encodeURIComponent(siteURL + "/from-facebook?type=city&id=" + location.id),
        status: _.template('Enjoying the sounds of SoundCloud Meetup {city} on {share_url} #scmeetup', {
          city: encodeURIComponent(location.city || location.country),
          share_url: encodeURIComponent(locations.shareURL(location))
        })
      })
  };

  locations.calcRadius = function(location) {
    var zoom = (!!map && map.zoom) || mapOptions.zoom;
    var level = (mapOptions.maxZoom - zoom)  * 10000;
    return (location.track_counter / locations.maxTracks) * level + 15000;
  };

  locations.saveCache = function() {
    cache.set('locations', JSON.stringify(locations));
  };

  locations.find = function(id){
    return _(locations.all).detect(function(loc) {
      return loc.id == id;
    });
  };

  locations.show = function() {
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
              location_link: locations.shareURL(location),
              location_twitter_share: locations.twitterShareURL(location),
              location_facebook_share: locations.facebookShareURL(location),
              track_title: location.tracks[0].title.substring(0, 60),
              track_avatar: _.template('<img class="avatar" src="{avatar_src}" alt="avatar">', {
                avatar_src: avatar.for_track(location.tracks[0], 'large')
              }),
              track_artist: _.template('<a href="{user_permalink}" target="_blank">{user_name}</a>', {
                user_permalink: location.tracks[0].user.permalink_url,
                user_name: location.tracks[0].user.username
              }),
              track_time: fuzzyTime(location.tracks[0].created_at),
              track_list: _(location.tracks).map(function(track) {
                return _.template('<li id="mini{mini_track_id}" class="mini-artwork" style="background-image: url({artwork_src});"></li>', {
                  mini_track_id: track.id,
                  artwork_src: avatar.for_track(track, 'small')
                });
              }).join('')
            });

            if (!!infoWindow) {
              infoWindow.close();
              google.maps.event.clearInstanceListeners(infoWindow);
            }
            infoWindow = new google.maps.InfoWindow({
              position: circles[location.id].center,
              content: '<div class="bubble">' + bubble_html + '</div>'
            });

            google.maps.event.addListenerOnce(infoWindow, 'domready', function() {
              player.activate(location, 0);
              player.play();

              $('.play-button').live('click', player.play);

              $('.share-link').live('click', function(e) {
                e.preventDefault();
                $(this).after(_.template('<input type="text" value="{share_link}" readonly>', { share_link: locations.shareURL(location) }))
                       .delay(5000).next().remove();
              });

              $('.avatar').live('click', function(e) {
                var image = new Image();
                var old_content = infoWindow.content;
                image.onload = function() {
                  infoWindow.setContent(image);
                };
                image.src = avatar.format($(this).attr('src'), 't300x300');
                google.maps.event.addListenerOnce(infoWindow, 'closeclick', function() {
                  infoWindow.setContent(old_content);
                  infoWindow.open(map);
                });
              });
            });
            infoWindow.open(map);
          });

          google.maps.event.addListener(circles[location.id], 'mouseover', function() {
            circles[location.id].setOptions({ zIndex: 1E9 });
          })

          if (location.id == id)
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

  var player = {
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
    playPrevious: function() {
      player.activate(player.data.location, player.data.current - 1);
    },
    playNext: function() {
      player.activate(player.data.location, player.data.current + 1);
    },
    seek: function(e) {
      e.preventDefault();
      var percent = (e.clientX - player.nodes.waveform.offset().left) / (player.nodes.waveform.width());
      if(player.sound.durationEstimate * percent < player.sound.durationEstimate)
        player.sound.setPosition(player.sound.durationEstimate * percent);
    }
  };

  player.init = function() { // Run only once
    player.init.initialized = player.init.initialized || false;
    if (player.init.initialized) return;
    player.nodes.player.find('.prev').click(player.playPrevious);
    player.nodes.player.find('.pause').click(player.toggle);
    player.nodes.player.find('.next').click(player.playNext);
    player.nodes.player.find('.waveform').click(player.seek);
    player.init.initialized = true;
  };

  player.activate = function(location, track_index) {
    if (!location.tracks[track_index]) return;
    else {
      var resume = true;
      player.pause();
      player.sound = undefined;
    }

    if (!player.nodes.container.is(':visible'))
      player.nodes.container.slideDown('fast');

    player.data = {};
    player.data.location = location;
    player.data.current = Number(track_index);

    window.soundManager.stopAll();

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
    var track = player.data.location.tracks[player.data.current];

    player.nodes.container.find('.metadata .metadata-html').html(_.template(tmpl, {
      track_permalink_url: track.permalink_url,
      track_title: track.title,
      user_permalink_url: track.user.permalink_url,
      user_name: track.user.username
    }));

    player.nodes.waveform.find('img').attr('src', track.waveform_url);

    if (!player.data.location.tracks[player.data.current + 1])
      player.nodes.player.find('.next').hide();
    else
      player.nodes.player.find('.next').show()

    if (!player.data.location.tracks[player.data.current + - 1])
      player.nodes.player.find('.prev').hide();
    else
      player.nodes.player.find('.prev').show();

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
        player.playNext()
      },
      onload: function() {
        player.nodes.loading.css('width', '100%');
      },
      onplay: function() {
        $('body').addClass("playing");
      },
      onresume: function() {
        $('body').addClass("playing");
      },
      onpause: function() {
        $('body').removeClass("playing");
      }
    });

    !!resume && player.play();
  }


  var map = new google.maps.Map($('#map_canvas')[0], _.extend(mapOptions, {
    center: (!!circles[id] && circles[id].center) || new google.maps.LatLng(52.52760, 13.40293)
  }));

  $(document).bind('forceResize', function(e) {
    $("#map_canvas").animate({
      height: $(window).height() - (player.nodes.container.is(':visible') ? player.nodes.container.height() : 0)
    }, 400, function() {
      google.maps.event.trigger(map, 'resize');
    });
  });

  $(window).resize(function() {
    $(document).trigger('forceResize');
  });

  $(document).trigger('forceResize');

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
    player.init();

    $(window).keyup(function(e) {
      var actions = {
        82: function() { // Random location!
          google.maps.event.trigger(circles[ locations.all[Math.floor(Math.random() * locations.all.length)].id ], 'click');
        },
        67: function() { // C key: Center and open bubble for closest location
          var closest = _(circles).min(function(circle) {
            return google.maps.geometry.spherical.computeDistanceBetween(map.getCenter(), circle.center)
          });
          !closest.getBounds().contains(map.getCenter()) && google.maps.event.trigger(closest, 'click');
        },
        37: player.playPrevious,
        32: player.toggle,
        39: player.playNext
      };
      actions.hasOwnProperty(e.keyCode) && actions[e.keyCode].call();
    });

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
        $("#about-box").fadeIn();
      })
    }
    else {
      locations.show();
      $("#about-box").fadeIn();
    }
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
