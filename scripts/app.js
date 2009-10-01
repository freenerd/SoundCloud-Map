/*Copyright (c) 2009 Johan Uhle

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

/* Initialize SoundManager */
soundManager.flashVersion = 9;
soundManager.useConsole = true;
soundManager.consoleOnly = true;
soundManager.debugMode = false;
soundManager.defaultOptions.multiShot = false;
soundManager.url = "/scripts/soundmanager2_flash9.swf";

soundManager.onload = function() {
  // soundManager is ready to use (create sounds and so on)
  // init the player app
  var map;
	var markerOptions = [];
	var icons = [];
	var locations = []; // all locations
  var loading = $("#player .loading");
  var progress = $("#player .progress");
  var position = $('#player .position');
  var duration = $('#player .duration');

  var sound = null;
  var playerIsVisible = false;
  var genre = "";
  
  var FOOTER_HEIGHT = 180;
  var PLAYER_HEIGHT = 80;

  if (GBrowserIsCompatible()) {
    map = new GMap2($("#map_canvas")[0]);
    $("#map_canvas").height($(window).height()-PLAYER_HEIGHT);
    map.checkResize();
		map.addControl(new GSmallZoomControl());
    map.setCenter(new GLatLng(-10.973349, 26.875), 2);
		map.setMapType(G_PHYSICAL_MAP);  
		map.enableScrollWheelZoom();	      
	}                                          
	
	// window resize handler
	$(window).resize(function() {
    $("#map_canvas").height($(window).height()-(playerIsVisible ? FOOTER_HEIGHT : PLAYER_HEIGHT));
    map.checkResize();
	});	

	// Different Sized Icons for the Marker. 1 is small. 3 is big
	icons[0] = new GIcon(G_DEFAULT_ICON);
  icons[0].image = "images/sc_marker_1.png";
  icons[0].iconSize = new GSize(4, 4);
  icons[0].shadow = null;
  icons[0].iconAnchor = new GPoint(4, 4);
  icons[0].infoWindowAnchor = new GPoint(4, 0);
	icons[0].imageMap = [ 0,0, 4,0, 4,4, 0,4 ];
	markerOptions[0] = { icon:icons[0] };
	
	icons[1] = new GIcon(G_DEFAULT_ICON);
  icons[1].image = "images/sc_marker_2.png";
  icons[1].iconSize = new GSize(6, 6);
  icons[1].shadow = null;
  icons[1].iconAnchor = new GPoint(6, 6);
  icons[1].infoWindowAnchor = new GPoint(6, 0); 
	icons[1].imageMap = [ 0,0, 6,0, 6,6, 0,6 ]; 
	markerOptions[1] = { icon:icons[1] };   
	
	icons[2] = new GIcon(G_DEFAULT_ICON);
  icons[2].image = "images/sc_marker_3.png";
  icons[2].iconSize = new GSize(11, 11);
  icons[2].shadow = null;
  icons[2].iconAnchor = new GPoint(11, 11);
  icons[2].infoWindowAnchor = new GPoint(11, 0);
	icons[2].imageMap = [ 0,0, 11,0, 11,11, 0,11 ];
	markerOptions[2] = { icon:icons[2] };

	icons[3] = new GIcon(G_DEFAULT_ICON);
  icons[3].image = "images/sc_marker_4.png";
  icons[3].iconSize = new GSize(17, 17);
  icons[3].shadow = null;
  icons[3].iconAnchor = new GPoint(17, 17);
  icons[3].infoWindowAnchor = new GPoint(17, 0);
	icons[3].imageMap = [ 0,0, 17,0, 17,17, 0,17 ];
	markerOptions[3] = { icon:icons[3] };

	icons[4] = new GIcon(G_DEFAULT_ICON);
  icons[4].image = "images/sc_marker_5.png";
  icons[4].iconSize = new GSize(24, 24);
  icons[4].shadow = null;
  icons[4].iconAnchor = new GPoint(24, 24);
  icons[4].infoWindowAnchor = new GPoint(24, 0);
	icons[4].imageMap = [ 0,0, 24,0, 24,24, 0,24 ];
	markerOptions[4] = { icon:icons[4] };

   // about box closable
  $("#about-box a.close").click(function(ev) {
    $("#about-box").fadeOut();
    ev.preventDefault();
  });    
                        
	// about box openable
  $("a#about").click(function(ev) {
    $("#about-box").fadeIn();
    ev.preventDefault();
  });  
     
	// about box closes when action on myp
	GEvent.addListener(map, "movestart", function() {
	  $("#about-box").fadeOut();
	}); 

	GEvent.addListener(map, "click", function() {
	  $("#about-box").fadeOut();
	});	                          
	
	GEvent.addListener(map, "zoomend", function() {
	  $("#about-box").fadeOut();
	});

	// genre buttons
	$(".genres a").click(function(ev) {
	  $(".genres .active").removeClass("active");
	  $(this).addClass("active");
	  removeAllMarkers();
	  loadLocations($(this).attr("data")); // load locations from the genre
	  return false;
	});
	
	// load all locations for a given genre
	function loadLocations(g) {
	  genre = g;
    $.getJSON("/api/locations/?genre=" + genre,function(locs) {
      $.each(locs,function(i,l) {
        setupLocation(l);
      });
    });
	}

  // set up an individual locations marker + popup
  function setupLocation(l) {
    // set the size of the dot based on how many tracks found in the location
		var option = 0;
		if (l.track_counter >= 10 && l.track_counter < 40) {
			option = 1;
		} else if (l.track_counter >= 40 && l.track_counter < 60) {
		 	option = 2;
		} else if (l.track_counter >= 60 && l.track_counter < 80) {
			option = 3;
		} else if (l.track_counter >= 80) {
			option = 4;
		};
		
		// if city field is empty, replace it with country
		if (l.city == "None") {
		  l.city = l.country;
		};
		
    // add the location marker
    l.marker = new GMarker(new GPoint(l.lon,l.lat), markerOptions[option]);
    GEvent.addListener(l.marker, "click", function() {
      // load all tracks in the location
  	  $.getJSON("/api/tracks/?genre=" + genre + "&location=" + l.id + "&limit=1",function(tracks) {
  	    l.first_track = tracks[0];
  	    tracks[0].loc = l;
  	    
        l.html = $('#bubble-template')
          .clone()
          .attr('id', 'bubble' + tracks[0].id)
					.find('.city span.city-track-counter').html(l.track_counter).end()
					.find('.city span.city-name').html(l.city).end()
          .find('.title').html(tracks[0].title).end()
          .find('.avatar').attr("src",(tracks[0].artwork_url ? tracks[0].artwork_url : tracks[0].user.avatar_url)).end()
          .find('ul li span.artist').html("<a href='" + tracks[0].user.permalink_url + "'>" + tracks[0].user.username + "</a>").end()
          .find('ul li span.time').html(fuzzyTime(tracks[0].created_minutes_ago) + " ago").end()
          .find('a.play-button').bind('click',tracks[0],showPlayer).end();

        // hide avatar if default user image is shown
        if(l.html.find(".avatar").attr("src").search(/default/) != -1) {
          l.html.find(".avatar").hide();
        }

        // load more tracks from the same city
        GEvent.clearListeners(l.marker,'infowindowopen');
        GEvent.addListener(l.marker, "infowindowopen", function() {
          $.getJSON("/api/tracks/?location=" + l.id + "&genre=" + genre + "&limit=10",function(extraTracks) {
            // clear the tracks list
            $("#bubble" + l.first_track.id).find('.tracks-list').html("");

            // add the new ones
            $.each(extraTracks,function(i,t) {
              $("#bubble" + l.first_track.id)
                .find('.tracks-list').append("<li class='mini-artwork'><a href='' style='background-image:" + artworkBgImage(t) + "'>track</a></li>").end()

                .find('.tracks-list .mini-artwork:last a').click(function() {

                  // highlight current image                  
                  $(this).parents("ul.tracks-list").find(".mini-artwork a").removeClass("active");
                  $(this).addClass("active");
                  
                  $("#bubble" + l.first_track.id)
                    .find('.title').html(t.title).end()
                    .find('.avatar').attr("src",(t.artwork_url ? t.artwork_url : t.user.avatar_url)).end()
                    .find('ul li span.artist').html("<a href='" + t.user.permalink_url + "'>" + t.user.username + "</a>").end()
                    .find('ul li span.time').html(fuzzyTime(t.created_minutes_ago) + " ago").end()
                    .find('a.play-button').bind('click',t,showPlayer).end();
                  return false;
                });
            });

            // highlight the first mini image
            $("#bubble" + l.first_track.id).find('.tracks-list .mini-artwork:first a').addClass("active");

            // if there's only one, then hide it
            if($("#bubble" + l.first_track.id).find('.tracks-list .mini-artwork a').length == 1) {
              $("#bubble" + l.first_track.id).find('.tracks-list').hide();              
            }

          });
        });

        // auto-play the first track
        // stop();
        // $("a.play-button:first",l.html).click();   

        l.marker.openInfoWindow(l.html[0]);

  	  });
      
    });
    map.addOverlay(l.marker);
    locations.push(l);
  }

  // helper to pick correct css bg url for mini artworks
  function artworkBgImage(t) {
    var artwork = (t.artwork_url ? t.artwork_url.replace(/large/,"small") : t.user.avatar_url.replace(/large/,"small"));
    // hide avatar if default user image is shown
    if(artwork.search(/default/) != -1) {
      artwork = "none";
    } else {
      artwork = "url(" + artwork + ")";
    }
    return artwork;
  }

  // throttling function to minimize redraws caused by soundmanager
  function throttle(delay, fn) {
    var last = null,
        partial = fn;

    if (delay > 0) {
      partial = function() {
        var now = new Date(),
            scope = this,
            args = arguments;

        // We are the last call made, so cancel the previous last call
        clearTimeout(partial.futureTimeout);

        if (last === null || now - last > delay) { 
          fn.apply(scope, args);
          last = now;
        } else {
          // guarentee that the method will be called after the right delay
          partial.futureTimeout = setTimeout(function() { fn.apply(scope, args); }, delay);
        }
      };
    }
    return partial;
  };

  // next random track
  $('#player .next').click(function(e) {
    stop();
    playRandom();
    return false;
  });

  // prev random track
  $('#player .prev').click(function(e) {
    playRandom();
    return false;
  });
  
  // pause track
  $('#player .pause').click(function(e) {
    togglePlay();
    return false;
  });
  
  // waveform seeking
  $("#player .waveform").click(function(ev) {
    var percent = (ev.clientX-$("#player .waveform").offset().left)/($("#player .waveform").width());
    if(sound.durationEstimate*percent < sound.durationEstimate) {
      sound.setPosition(sound.durationEstimate*percent);        
    }
  });

  // play
  function play() {
    if(sound) {
      sound.paused ? sound.resume() : sound.play();
      $('body').addClass("playing");
    }
  };

  // toggle play
  function togglePlay() {
    if($('body').hasClass("playing")) {
    }
    $('body').hasClass("playing") ? stop() : play();
  };

  // stop
  function stop() {
    if(sound) {
      $('body').removeClass("playing");
      sound.pause();
    }
  };

  // format millis into MM.SS
  var formatMs = function(ms) {
    var s = Math.floor((ms/1000) % 60);
    if (s < 10) { s = "0"+s; }
    return Math.floor(ms/60000) + "." + s;
  };

  // shows the track player with a given track
  function showPlayer(e) {
    if(!playerIsVisible) { // show player if it's hidden
      playerIsVisible = true;
      $("#player-container").slideDown();
      $("#map_canvas").animate({height:$(window).height()-FOOTER_HEIGHT},500,function() {
        map.checkResize();
      });
    }

    var track = (e.data ? e.data : e);
    
    if(window.soundManager.swfLoaded) {
      window.soundManager.stopAll();
    };
    
    $("#player-container .show-on-map").unbind('click');
    $("#player-container .show-on-map").click(function() {
      map.panTo(new GLatLng(track.location.lat,track.location.lon));
      GEvent.trigger(track.loc.marker,'click');
      return false;
    });
    
    // set up share to twitter, no url shortener yet
    $("#player-container .share-on-twitter").attr("href","http://twitter.com/home/?source=soundcloud&status=" + encodeURIComponent(track.title) + " by " + encodeURIComponent(track.user.username) + " http://tracksonamap.com/%23track-" + track.id + " via+%23tracksonamap")
    
    $("#player-container .metadata").html("<a target='_blank' href='" + track.user.permalink_url + "/" + track.permalink + "'>" + track.title + "</a>" + " uploaded by <a target='_blank' href='" + track.user.permalink_url + "'>" + track.user.username + "</a>");
    
		$("#player-container #player .waveform img").attr("src", track.waveform_url);
		
    sound = soundManager.createSound({
      id: track.id,
      url: track.stream_url + "?oauth_consumer_key=FhPCTC6rJGetkMIcLwI9A",
      whileloading : throttle(100,function() {
        loading.css('width',(sound.bytesLoaded/sound.bytesTotal)*100+"%");
      }),
      whileplaying : throttle(100,function() {
        progress.css('width',(sound.position/track.duration)*100+"%");
        position.html(formatMs(sound.position));
        duration.html(formatMs(track.duration));
      }),
      onfinish : function() {
        $("body").removeClass("playing");
        sound.setPosition(0);
        playRandom();
      },
      onload : function () {
        loading.css('width',"100%");
      }
    });
    
    // set loading bar to 100% if sound is already loaded
    if(sound.bytesLoaded == sound.bytesTotal) {
      loading.css('width',"100%");      
    }

    togglePlay();
    
    return false;
  }

  // remove all location markers
	function removeAllMarkers() {
    $.each(locations, function( intIndex, l ) {
     GEvent.clearInstanceListeners(l.marker);
     map.removeOverlay(l.marker);
    });
    locations = []; // reset the main locations array
	}

  // plays a random location
	function playRandom() {
    GEvent.trigger(locations[Math.floor(Math.random()*locations.length)].marker,'click'); // trigger a click on a random marker
	}   

	// display a human readable time
	function fuzzyTime(minutes) { 
		if(minutes <= 60) return minutes.toString() + " minutes";
		if(minutes > 60 && minutes <= 1440) return (Math.floor(minutes/60)).toString() + " hours";
		if(minutes > 1440 && minutes <= 10080) return (Math.floor(minutes/(60*24))).toString() + " days";
		if(minutes > 10080 && minutes <= 70560) return (Math.floor(minutes/(60*24*7))).toString() + " weeks";
		if(minutes > 70560) return (Math.floor(minutes/(60*24*30))).toString() + " months";       		
	}

  // main keyboard listener
  $(window).keydown(function(ev) {
    if(ev.keyCode === 32) { // start/stop play
      togglePlay();
    } else if (ev.keyCode === 39) { // arrow next, play next if playing
      stop();
      playRandom();
    } else if (ev.keyCode === 37) { // arrow prev, play prev if playing
      // not implemented
    }
  });
  
	// show about box, if on live server and user hasn't seen it for 24 hours
  if(location.href.split(".").length > 1 && !$.cookie('viewed_intro') == '1'){
    $.cookie('viewed_intro', '1', { expires: 1 });
    $("#about-box").fadeIn();
  }

	// start the app
  loadLocations("all");
  
  //pop up the track that was shared if /#track-123123 detected
  if(location.hash && location.hash.search(/track/) != -1) {
    var trackId = location.hash.split("-")[1];
    $.getJSON("/api/tracks/"+ trackId,function(track) {
      showPlayer(track[0]);
      setupLocation(track[0].location);
      GEvent.trigger(locations[locations.length-1].marker,'click'); // trigger a click on a random marker
    });
  }

}
