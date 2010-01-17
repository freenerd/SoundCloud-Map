/*Copyright (c) 2009 Johan Uhle, Eric Wahlforss

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
  var maxTracksInLocation = 5; // max tracks on a specific location

  var sound = null;
  var playerIsVisible = false;
  var genre = "";
  
  var FOOTER_HEIGHT = 180;
  var PLAYER_HEIGHT = 80;

  if (GBrowserIsCompatible()) {
    map = new GMap2($("#map_canvas")[0]);
		map.addControl(new GSmallZoomControl());
		map.setMapType(G_PHYSICAL_MAP);  
    map.setCenter(new GLatLng(-10.973349, 26.875), 2);		
		map.enableScrollWheelZoom();	      
    $("#map_canvas").height($(window).height()-PLAYER_HEIGHT);
    map.checkResize();    
	}                                          
	
	// window resize handler
	$(window).resize(function() {
    $("#map_canvas").height($(window).height()-(playerIsVisible ? FOOTER_HEIGHT : PLAYER_HEIGHT));
    map.checkResize();
	});	

  // 
  // Begin Connect with SoundCloud
  //

  var options = { 
      'request_token_endpoint': '/soundcloud-connect/request-token/',
      'access_token_endpoint': '/soundcloud-connect/access-token/',
      'callback': function(query_obj){}
    };
    
  SC.Connect.prepareButton($('#connect-with-sc'),options);

	// followers / following buttons
	$("#connect-with-sc-followers").click(function(ev) {
	  $(".genres .active").removeClass("active");
	  $(".cwsc .active").removeClass("active");
	  $(this).addClass("active");
	  removeAllMarkers();
	  loadLocations($(this).attr("data")); // load locations from the genre
	  return false;
	});

  // 
  // End Connect with SoundCloud
  //

	// Different sized icons for the markers. 0 is small, 4 is big.
	icons[0] = new GIcon(G_DEFAULT_ICON);
  icons[0].image = "images/sc_marker_1.png";
  icons[0].iconSize = new GSize(4, 4);
  icons[0].shadow = null;
  icons[0].iconAnchor = new GPoint(2, 2);
  icons[0].infoWindowAnchor = new GPoint(4, 0);
	icons[0].imageMap = [ 0,0, 4,0, 4,4, 0,4 ];
	markerOptions[0] = { icon:icons[0] };
	
	icons[1] = new GIcon(G_DEFAULT_ICON);
  icons[1].image = "images/sc_marker_2.png";
  icons[1].iconSize = new GSize(6, 6);
  icons[1].shadow = null;
  icons[1].iconAnchor = new GPoint(3, 3);
  icons[1].infoWindowAnchor = new GPoint(6, 0); 
	icons[1].imageMap = [ 0,0, 6,0, 6,6, 0,6 ]; 
	markerOptions[1] = { icon:icons[1] };   
	
	icons[2] = new GIcon(G_DEFAULT_ICON);
  icons[2].image = "images/sc_marker_3.png";
  icons[2].iconSize = new GSize(11, 11);
  icons[2].shadow = null;
  icons[2].iconAnchor = new GPoint(6, 6);
  icons[2].infoWindowAnchor = new GPoint(11, 0);
	icons[2].imageMap = [ 0,0, 11,0, 11,11, 0,11 ];
	markerOptions[2] = { icon:icons[2] };

	icons[3] = new GIcon(G_DEFAULT_ICON);
  icons[3].image = "images/sc_marker_4.png";
  icons[3].iconSize = new GSize(17, 17);
  icons[3].shadow = null;
  icons[3].iconAnchor = new GPoint(9, 9);
  icons[3].infoWindowAnchor = new GPoint(17, 0);
	icons[3].imageMap = [ 0,0, 17,0, 17,17, 0,17 ];
	markerOptions[3] = { icon:icons[3] };

	icons[4] = new GIcon(G_DEFAULT_ICON);
  icons[4].image = "images/sc_marker_5.png";
  icons[4].iconSize = new GSize(24, 24);
  icons[4].shadow = null;
  icons[4].iconAnchor = new GPoint(12, 12);
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
     
	// about box closes when action on map
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
		
	// 
	var offset = 0;
	var LIMIT = 10;
	
	// simple recursive algorithm to progressively load more tracks over ajax
	function loadLocationsRecursive(locs) {
	  // base case: never pull more than 200 tracks, and stop pulling when locs returns 0 locations
    if(offset < 200 && (!locs || locs.length > 0)) {
      $.getJSON("/api/locations/?&limit=" + LIMIT + "&offset=" + offset + "&genre=" + genre,loadLocationsRecursive);
      if(locs) {
        $.each(locs,function(i,l) {
          var delay = i*30;
          setTimeout(function() {
            setupLocation(l);
          },delay);
        });
      }
      offset += LIMIT;
    } else {
      // execute callback here
    }
	};
	
	// load all locations for a given genre
	function loadLocations(g,callback) {
	  genre = g;
    
    // first get the no of tracks for the location with the most number of tracks, then recursively load locations
    $.getJSON("/api/locations/maxtracks?genre=" + genre,function(maxtracks) {
      maxTracksInLocation = maxtracks.max_tracks;
      // reset offset counter
      offset = 0;
      loadLocationsRecursive();
    });	  

    // callback, needed for e.g. autoplay
    //   if(callback) { // execute a callback fn
    //     callback.apply();        
    //   }
	}

  // set up an individual locations marker + popup
  function setupLocation(l, trackToShowFirst) {
    // set the size of the dot based on how many tracks found in the location
		var option = 0;
		
		// figure out the relative size of the dot
		var locRelSize = l.track_counter/maxTracksInLocation;
		
		// find out size of dot based on relative size
		if (locRelSize >= 0 && locRelSize < 0.05) {
			option = 1;
		} else if (locRelSize >= 0.05 && locRelSize < 0.2) {
		 	option = 2;                                  
		} else if (locRelSize >= 0.2 && locRelSize < 0.5) {
			option = 3;
		} else if (l.track_counter >= 0.5) {
			option = 4;
		};
		
		// if city field is empty, replace it with country
		if (l.city == "None") {
		  l.city = l.country;
		};
		
    // add the location marker
    l.marker = new GMarker(new GPoint(l.lon,l.lat), markerOptions[option]);
    GEvent.addListener(l.marker, "click", function() {
      if(!l.marker.setupDone) {
      
        // load all tracks in the location, start with the first

        var tracksUrl = "/api/tracks/";
        if(trackToShowFirst) { // load the track to show first
          tracksUrl += trackToShowFirst;
        } else { // load the first track from the location
          tracksUrl += "?genre=" + genre + "&location=" + l.id + "&limit=1";
        }
    	  $.getJSON(tracksUrl,function(tracks) {
    	    l.firstTrack = tracks[0];
    	    tracks[0].loc = l; 
    	    
    	    
  				var linkToBeShared = "http://tracksonamap.com/#city-" + l.id;

  		    // set up share to twitter, no url shortener yet
  				var twitterShareLink = "I am listening to " + l.city + " on " + linkToBeShared + " via @tracksonamap";                                          
  			  twitterShareLink = "http://twitter.com/home/?source=soundcloud&status=" + encodeURIComponent(twitterShareLink);
          
          var facebookLinkToBeShared = "http://tracksonamap.com/from-facebook?type=city&id=" + l.id
  				// set up share to Facebook
  				var facebookShareLink = "I am listening to " + l.city;                                                                          
  				facebookShareLink = "http://www.facebook.com/share.php?u=" + encodeURIComponent(facebookLinkToBeShared) + "&t=" + encodeURIComponent(facebookShareLink);    	    
    	    
  	    
          l.html = $('#bubble-template')
            .clone()
            .attr('id', 'bubble' + tracks[0].id)
  					.find('.city span.city-track-counter').html(l.track_counter).end()
  					.find('.city span.city-name').html(l.city).end()
            .find('.title').html(tracks[0].title.substring(0,60)).end()
            .find('.avatar').attr("src",(tracks[0].artwork_url ? tracks[0].artwork_url : tracks[0].user.avatar_url)).end()
            .find('ul li span.artist').html("<a href='" + tracks[0].user.permalink_url + "'>" + tracks[0].user.username + "</a>").end()
            .find('ul li span.time').html(fuzzyTime(tracks[0].created_minutes_ago) + " ago").end()
            .find('a.play-button').bind('click',tracks[0],showPlayer).end()
  					.find('.city .share-on-twitter').attr("href", twitterShareLink).end()
  					.find('.city .share-on-facebook').attr("href", facebookShareLink).end()
  			    .find('.city .share-link').attr('href',linkToBeShared).end()
  					.find('.city .share-link').click(function() {
  			      $("#share-box > div:first")
  			        .clone()
  			        .find("a.close").click(function() {
  			          	$(this).parents("div.share-box").fadeOut(function() {
  			            $(this).remove();
  			          });
  			          return false;
  			        }).end()
  			        .find("input").val(this.href).end()
  							.find("h1 .typ").html("City").end()
  							.find("p .typ").html("city").end()
  			        .appendTo("body")
  			        .fadeIn(function() {
  			          $(".share-box input").focus().select();
  			        });          
  			      return false;
  			    }).end();

          // hide avatar if default user image is shown
          if(l.html.find(".avatar").attr("src").search(/default/) != -1) {
            l.html.find(".avatar").hide();
          }

          // load more tracks from the same city
          GEvent.clearListeners(l.marker,'infowindowopen');
          GEvent.addListener(l.marker, "infowindowopen", function() {
            if(!l.marker.setupDone) {
          
              // clear the tracks list
              $("#bubble" + l.firstTrack.id).find('.tracks-list').html("");
            
              $.getJSON("/api/tracks/?location=" + l.id + "&genre=" + genre + "&limit=9",function(extraTracks) {
            
                if(trackToShowFirst) { // make sure that the first track loaded in the list is the track first shown in the bubble (used for track permalinks)
              
                  // remove occurances of the first track
                  $.each(extraTracks,function(i,e) {
                    if(e && e.id == l.firstTrack.id) {
                      extraTracks.splice(i,1);
                    }
                  });
              
                  extraTracks = tracks.concat(extraTracks); // add it first in the array
              
                  if(extraTracks.length > 10) { // make sure the list is not longer than 10 tracks
                    extraTracks = extraTracks.slice(0,10);
                  }
                }

                // add the new ones
                $.each(extraTracks,function(i,t) {
                  // add a reference to the location also for all the extra tracks
                  t.loc = l;
                  $("#bubble" + l.firstTrack.id)
                    .find('.tracks-list').append("<li class='mini-artwork'><a href='' style='background-image:" + artworkBgImage(t) + "'>track</a></li>").end()

                    .find('.tracks-list .mini-artwork:last a').click(function() {

                      // highlight current image                  
                      $(this).parents("ul.tracks-list").find(".mini-artwork a").removeClass("active");
                      $(this).addClass("active");

                      $("#bubble" + l.firstTrack.id)
                        .find('.title').html(t.title.substring(0,60)).end()
                        .find('.avatar').attr("src",(t.artwork_url ? t.artwork_url : t.user.avatar_url)).end()
                        .find('ul li span.artist').html("<a href='" + t.user.permalink_url + "'>" + t.user.username + "</a>").end()
                        .find('ul li span.time').html(fuzzyTime(t.created_minutes_ago) + " ago").end()
                        .find('a.play-button').bind('click',t,showPlayer).end();
                      return false;
                    });
                });

                // highlight the first mini image
                $("#bubble" + l.firstTrack.id).find('.tracks-list .mini-artwork:first a').addClass("active");

                // if there's only one, then hide it
                if($("#bubble" + l.firstTrack.id).find('.tracks-list .mini-artwork a').length == 1) {
                  $("#bubble" + l.firstTrack.id).find('.tracks-list').hide();              
                }

              });
            
              l.marker.setupDone = true; // next time we don't have to set up the bubble
            }
            
          }); // end open info window setup

          // auto-play the first track, if no track is playing
          if(!$('body').hasClass("playing")) {
            $("a.play-button:first",l.html).click();   
          }
          
          // now that we've finished the ajax calls, we can show the info window
          l.marker.openInfoWindow(l.html[0]);

    	  });
        
      } else { // bubble already set up, so just open info window
        // auto-play the first track, if no track is playing
        if(!$('body').hasClass("playing")) {
          $("a.play-button:first",l.html).click();   
        }
        l.marker.openInfoWindow(l.html[0]);
      }      
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

		var linkToBeShared = "http://tracksonamap.com/#track-" + track.id;
		
		// set up share link (share box)
    $("#player-container .share-link").attr('href',linkToBeShared);	
    $("#player-container .share-link").unbind('click');
		$('#player-container .share-link').click(function() {
      $("#share-box > div:first")
        .clone()
        .find("a.close").click(function() {
          $(this).parents("div.share-box").fadeOut(function() {
            $(this).remove();
          });
          return false;
        }).end()
        .find("input").val(this.href).end()
        .appendTo("body")
        .fadeIn(function() {
          $(".share-box input").focus().select();
        });          
      return false;
    });    
		
    // set up share to twitter, no url shortener yet
		var twitterShareLink = track.title  + " by " + track.user.username + " on " + linkToBeShared + " via @tracksonamap";                                          
	  twitterShareLink = "http://twitter.com/home/?source=soundcloud&status=" + encodeURIComponent(twitterShareLink);
    $("#player-container .share-on-twitter").attr("href", twitterShareLink);
   
		// set up share to Facebook
		var facebookLinkToBeShared = "http://www.tracksonamap.com/from-facebook?type=track&id=" + track.id
		var facebookShareLink = "Tracks On A Map: " + track.title  + " by " + track.user.username;                                                                          
		facebookShareLink = "http://www.facebook.com/share.php?u=" + encodeURIComponent(facebookLinkToBeShared) + "&t=" + encodeURIComponent(facebookShareLink);
    $("#player-container .share-on-facebook").attr("href", facebookShareLink);		

    $("#player-container .metadata div:last").html("<a target='_blank' href='" + track.user.permalink_url + "/" + track.permalink + "'>" + track.title + "</a>" + " uploaded by <a target='_blank' href='" + track.user.permalink_url + "'>" + track.user.username + "</a>");
    
		$("#player-container #player .waveform img").attr("src", track.waveform_url);
		
		// show the spinner
		$(".waveform img, .waveform .loading, .waveform .progress").css("visibility","hidden");
		$(".waveform .spinner").css("visibility","visible");
		
    sound = soundManager.createSound({
      id: track.id,
      url: track.stream_url + "?oauth_consumer_key=FhPCTC6rJGetkMIcLwI9A",
      whileloading : throttle(100,function() {
        loading.css('width',(sound.bytesLoaded/sound.bytesTotal)*100+"%");
      }),
      whileplaying : throttle(100,function() {
        if($(".waveform img").css("visibility") == "hidden") { // show spinner if track has not started to load
      		$(".waveform img, .waveform .loading, .waveform .progress").css("visibility","visible");
      		$(".waveform .spinner").css("visibility","hidden");          
        }
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

    play();
    
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
		// show the spinner
		$(".waveform img, .waveform .loading, .waveform .progress").css("visibility","hidden");
		$(".waveform .spinner").css("visibility","visible");

	  var randLoc = Math.floor(Math.random()*locations.length);
    GEvent.trigger(locations[randLoc].marker,'click'); // trigger a click on a random marker
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

	// start the app, then play a random track
  loadLocations("all",function() {
    playRandom();
  });
  map.setCenter(new GLatLng(-10.973349, 26.875), 2);		
  //pop up the track that was shared if /#track-123123 detected
  if(location.hash && location.hash.search(/track|city/) != -1) {
    var id = location.hash.split("-")[1];
    var q = "/api/tracks/";
    if(location.hash.search(/track/) != -1) { // track permalink
      q += id;
    } else if(location.hash.search(/city/) != -1) { // location permalink
      q += "?limit=1&location="+ id;
    }
    $.getJSON(q,function(track) {
      showPlayer(track[0]);      
      map.setZoom(5);      
      setupLocation(track[0].location,track[0].id);
      GEvent.trigger(locations[locations.length-1].marker,'click'); // play the track (is this really clean?)
    });      
  }
  
  if(location.hash && location.hash.search(/scconnect/) != -1) {
  var q = "/api/soundcloud-connect/followers/";
  $.getJSON(q,function(location) {
    $.each(location,function(i,l) {
      setupLocation(l);
      });
    });
  }
}
