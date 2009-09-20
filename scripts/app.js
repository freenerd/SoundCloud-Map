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
// soundManager.useHighPerformance = false;

/* Initialize Google Maps */
$(function() {
  var map;
  var icon1;
  var icon2;
  var icon3;

  if (GBrowserIsCompatible()) {
    map = new GMap2($("#map_canvas")[0]);
    $("#map_canvas").height($(window).height()-40);
    map.checkResize();
		map.addControl(new GSmallZoomControl());
    map.setCenter(new GLatLng(-10.973349, 26.875), 2);
		map.setMapType(G_PHYSICAL_MAP);        
	}                                          
	
	$(window).resize(function() {
    $("#map_canvas").height($(window).height()-(playerIsVisible ? 140 : 40));
    map.checkResize();
	});
	
	// Different Sized Icons for the Marker. 1 is small. 3 is big
	var icon1 = new GIcon(G_DEFAULT_ICON);
  icon1.image = "images/sc_marker_1.png";
  icon1.iconSize = new GSize(17, 17);
  icon1.shadow = null;
  icon1.iconAnchor = new GPoint(8, 8);
  icon1.infoWindowAnchor = new GPoint(17, 0);
	icon1.imageMap = [ 8,14, 4,11, 3,8, 4,4, 8,3, 12,5, 13,8, 12,12 ]; 
	markerOptions1 = { icon:icon1 };
	
	var icon2 = new GIcon(G_DEFAULT_ICON);
  icon2.image = "images/sc_marker_2.png";
  icon2.iconSize = new GSize(26, 26);
  icon2.shadow = null;
  icon2.iconAnchor = new GPoint(13, 	13);
  icon2.infoWindowAnchor = new GPoint(26, 0); 
	icon2.imageMap = [ 12,22, 6,19, 3,13, 5,5, 12,3, 19,6, 22,12, 19,20 ]; 
	markerOptions2 = { icon:icon2 };   
	
	var icon3 = new GIcon(G_DEFAULT_ICON);
  icon3.image = "images/sc_marker_3.png";
  icon3.iconSize = new GSize(43, 43);
  icon3.shadow = null;
  icon3.iconAnchor = new GPoint(21, 21);
  icon3.infoWindowAnchor = new GPoint(43, 0);
	icon3.imageMap = [ 20,37, 9,32, 4,21, 9,9, 20,5, 30,8, 37,20, 32,32 ];
	markerOptions3 = { icon:icon3 };        

	var tracks; // all tracks

  var loading = $("#player .loading");
  var progress = $("#player .progress");
  var sound;
  var playerIsVisible = false;

	// genre buttons
	$(".genres a").click(function(ev) {
	  $(".genres .active").removeClass("active");
	  $(this).addClass("active");
	  removeAllMarkers();
	  if($(this).attr("data") == 'all') {
  	  loadTracks('frontend-json/');
	  } else {
	    loadTracks('frontend-json/genre/' + $(this).attr("data"));
	  }
	  return false;
	});
	
	function loadTracks(url) {
		/*  This function takes a url to JSON data.
				It fetches the data and makes a bubble on the map for every track.
		*/
    $.getJSON(url, '', function(data) {
      tracks = data;
      if ( tracks.length < 1) return false;
      
      $.each( tracks,	function( intIndex, track ) {                     
				var option;
				if (track.tracks_in_location < 10) {
					option = markerOptions1;
				} else {
				 	if (track.tracks_in_location < 30) {
						option = markerOptions2;
					} else {
					 	option = markerOptions3;
					};  
				};
	
        track.marker = new GMarker(new GPoint(track.location_lat, track.location_lng), option);
        
        // hack to fix
				if (track.city == null) track.city = track.country;

        track.html = $('#bubble-template')
          .clone()
          .attr('id', 'bubble' + track.track_id)
					.find('.city span.city-track-counter').html(track.tracks_in_location).end()
					.find('.city span.city-name').html(track.city).end()
          .find('.title').html(track.title).end()
          .find('.avatar').attr("src",(track.artwork_url ? track.artwork_url : track.avatar_url)).end()
          .find('ul li span.artist').html("<a href='http://soundcloud.com/" + track.user_permalink + "'>" + track.username + "</a>").end()
          .find('ul li span.time').html(fuzzyTime(track.created_minutes_ago) + " ago").end()
          .find('a.play-button').bind('click',track,showPlayer).end();
        
        // hide avatar if default user image is shown
        if(track.html.find(".avatar").attr("src").search(/default/) != -1) {
          track.html.find(".avatar").hide();
        }

        GEvent.addListener(track.marker, "click", function() {
          track.marker.openInfoWindow(track.html[0]);
        });
        
        // load more tracks from the same city
        GEvent.addListener(track.marker, "infowindowopen", function() {
          $.getJSON("/frontend-json/location/" + track.location_lat + "/" + track.location_lng + "/50/",function(extraTracks) {
            // clear the tracks list
            $("#bubble" + track.track_id).find('.tracks-list').html("");
                        
            // add the new ones
            $.each(extraTracks,function(i,t) {
              $("#bubble" + track.track_id)
                .find('.tracks-list').append("<li class='mini-artwork'><a href='' style='background:url(" + (t.artwork_url ? t.artwork_url : t.avatar_url) + ")'>track</a></li>").end()
                .find('.tracks-list .mini-artwork:last a').click(function() {
                  
                  // highlight current image                  
                  $(this).parents("ul.tracks-list").find(".mini-artwork a").removeClass("active");
                  $(this).addClass("active");

                  $("#bubble" + track.track_id)
                    .find('.title').html(t.title).end()
                    .find('.avatar').attr("src",(t.artwork_url ? t.artwork_url : t.avatar_url)).end()
                    .find('ul li span.artist').html("<a href='http://soundcloud.com/" + t.user_permalink + "'>" + t.username + "</a>").end()
                    .find('ul li span.time').html(fuzzyTime(t.created_minutes_ago) + " ago").end()
                    .find('a.play-button').bind('click',t,showPlayer).end();
                  
                  return false;
                });              
            });
            
            // highlight the first mini image
            $("#bubble" + track.track_id).find('.tracks-list .mini-artwork:first a').addClass("active");
            
          });
        });
        
        map.addOverlay(track.marker);
      });
		});
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
      playRandom();
      return false;
  });

  // next random track
  $('#player .prev').click(function(e) {
      playRandom();
      return false;
  });
  
  // next random track
  $('#player .pause').click(function(e) {
      togglePlay();
      return false;
  });
  
  $("#player .waveform").click(function(ev) {
    var percent = (ev.clientX-$("#player .waveform").offset().left)/($("#player .waveform").width());
    if(sound.durationEstimate*percent < sound.durationEstimate) {
      sound.setPosition(sound.durationEstimate*percent);        
    }
  });

  function play() {
    if(sound) {
      sound.paused ? sound.resume() : sound.play();
      $('body').addClass("playing");
    }
  };

  function togglePlay() {
    $('body').hasClass("playing") ? stop() : play();
  };

  function stop() {
    if(sound) {
      sound.pause();
      $('body').removeClass("playing");
    }
  };

  // format millis into MM.SS
  var formatMs = function(ms) {
    var s = Math.floor((ms/1000) % 60);
    if (s < 10) { s = "0"+s; }
    return Math.floor(ms/60000) + "." + s;
  };

  function showPlayer(e) {
    if(!playerIsVisible) { // show player if it's hidden
      playerIsVisible = true;
      $("#player-container").slideDown();
      $("#map_canvas").animate({height:$(window).height()-140},500,function() {
        map.checkResize();
      });
    }

    var track = (e.data ? e.data : e);
    
    //$("#player-container").slideDown('slow');
    if(window.soundManager.swfLoaded) {
      window.soundManager.stopAll();
    };
    
    $("#player-container .show-on-map").click(function() {
      map.panTo(new GLatLng(parseInt(track.location_lat), parseInt(track.location_lng)));
      track.marker.openInfoWindow(track.html[0]);
      return false;
    });
    
    $("#player-container .metadata").html("<a href='http://soundcloud.com/" + track.user_permalink + "/" + track.permalink + "'>" + track.title + "</a>" + " uploaded by <a href='" + track.user_permalink + "'>" + track.username + "</a>");
    
    sound = soundManager.createSound({
      id: track.track_id,
      url: track.stream_url + "?oauth_consumer_key=FhPCTC6rJGetkMIcLwI9A",
      whileloading : throttle(100,function() {
        loading.css('width',(sound.bytesLoaded/sound.bytesTotal)*100+"%");
      }),
      whileplaying : throttle(100,function() {
        progress.css('width',(sound.position/sound.durationEstimate)*100+"%");
        $('#player .position').html(formatMs(sound.position));
        $('#player .duration').html(formatMs(sound.durationEstimate));
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

    play();
    
    return false;
  }

	function removeAllMarkers() {
    $.each(tracks, function( intIndex, track ) {
     GEvent.clearInstanceListeners(track.marker);
     map.removeOverlay(track.marker);
    });
    tracks = null;
	}

	function playRandom() {
	  var rand = Math.floor(Math.random()*tracks.length);
    tracks[rand].marker.openInfoWindow(tracks[rand].html[0]);
    showPlayer(tracks[rand]);
	}   
	
	function fuzzyTime(minutes) { 
		if(minutes <= 60) return minutes.toString() + " minutes";
		if(minutes > 60 && minutes <= 1440) return (Math.floor(minutes/60)).toString() + " hours";
		if(minutes > 1440 && minutes <= 10080) return (Math.floor(minutes/(60*24))).toString() + " days";
		if(minutes > 10080 && minutes <= 70560) return (Math.floor(minutes/(60*24*7))).toString() + " weeks";
		if(minutes > 70560) return (Math.floor(minutes/(60*24*30))).toString() + " months";       		
	}

	// start the app
  loadTracks('frontend-json/');

});
